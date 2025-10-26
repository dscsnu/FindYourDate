from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from app.core.llm_questionnaire import process_and_embed_chat, embed_full_chat, generate_next_question
from app.core.rate_limiter import rate_limiter

router = APIRouter(tags=["chat"])


class ChatMessage(BaseModel):
    q: str = Field(..., description="Question text")
    a: str = Field(..., description="Answer text")


class ChatHistoryRequest(BaseModel):
    user_email: str = Field(..., description="User's email")
    chat_history: List[ChatMessage] = Field(..., description="List of Q&A pairs")


class FullChatRequest(BaseModel):
    user_email: str = Field(..., description="User's email")
    chat_text: str = Field(..., description="Full chat conversation as text")


class ChatResponse(BaseModel):
    status: str
    message: str
    user_email: Optional[str] = None
    answers_processed: Optional[int] = None


class NextQuestionRequest(BaseModel):
    user_email: Optional[str] = Field(None, description="User's email (required for auto-embedding on completion)")
    chat_history: List[ChatMessage] = Field(
        default=[],
        description="List of previous Q&A pairs (empty array for first question)"
    )


class NextQuestionResponse(BaseModel):
    question: Optional[str] = Field(None, description="Next question text (None if complete)")
    is_complete: bool = Field(..., description="Whether questionnaire is complete")
    question_number: int = Field(..., description="Current question number")
    total_questions: int = Field(..., description="Total number of questions")
    category: Optional[str] = Field(None, description="Question category: 'personality' or 'social_energy'")
    message: Optional[str] = Field(None, description="Additional message if complete")
    note: Optional[str] = Field(None, description="Additional notes (e.g., fallback used)")
    embedding_status: Optional[str] = Field(None, description="Status of auto-embedding (success/error)")
    embedding_error: Optional[str] = Field(None, description="Error message if embedding failed")
    user_email: Optional[str] = Field(None, description="User email if embedded successfully")
    answers_processed: Optional[int] = Field(None, description="Number of answers processed in embedding")


@router.post("/embed-history", response_model=ChatResponse)
async def embed_chat_history(request: ChatHistoryRequest):
    """
    Process structured chat history (Q&A pairs) and store embeddings in Qdrant.
    """
    try:
        chat_history_dicts = [msg.dict() for msg in request.chat_history]
        
        result = process_and_embed_chat(
            user_id=request.user_email,
            chat_history=chat_history_dicts
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        return ChatResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {str(e)}")


@router.post("/embed-full-text", response_model=ChatResponse)
async def embed_full_chat_text(request: FullChatRequest):
    """
    Process full chat as single text string and store embeddings in Qdrant.
    """
    try:
        result = embed_full_chat(
            user_email=request.user_email,
            full_chat_text=request.chat_text
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        return ChatResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {str(e)}")


@router.post("/next-question", response_model=NextQuestionResponse)
async def get_next_question(request: NextQuestionRequest):
    try:
        # Rate limiting: 10 requests per 10 minutes (600 seconds) per user
        if request.user_email:
            is_limited, seconds_until_reset = rate_limiter.is_rate_limited(
                key=f"chat:{request.user_email}",
                max_requests=15,
                window_seconds=600
            )

            if is_limited:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Too many requests",
                        "message": f"Rate limit exceeded. Please try again in {seconds_until_reset} seconds.",
                        "retry_after": seconds_until_reset
                    }
                )

        chat_history_dicts = [msg.dict() for msg in request.chat_history]
        
        result = generate_next_question(
            chat_history=chat_history_dicts,
            user_email=request.user_email
        )
        
        return NextQuestionResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate question: {str(e)}"
        )
