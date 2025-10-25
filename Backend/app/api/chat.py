from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from app.core.llm_questionnaire import process_and_embed_chat, embed_full_chat, generate_next_question

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    q: str = Field(..., description="Question text")
    a: str = Field(..., description="Answer text")


class ChatHistoryRequest(BaseModel):
    user_id: int = Field(..., description="User's ID")
    chat_history: List[ChatMessage] = Field(..., description="List of Q&A pairs")


class FullChatRequest(BaseModel):
    user_id: int = Field(..., description="User's ID")
    chat_text: str = Field(..., description="Full chat conversation as text")


class ChatResponse(BaseModel):
    status: str
    message: str
    user_id: Optional[int] = None
    answers_processed: Optional[int] = None


class NextQuestionRequest(BaseModel):
    user_id: Optional[int] = Field(None, description="User's ID (required for auto-embedding on completion)")
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
    user_id: Optional[int] = Field(None, description="User ID if embedded successfully")
    answers_processed: Optional[int] = Field(None, description="Number of answers processed in embedding")


@router.post("/embed-history", response_model=ChatResponse)
async def embed_chat_history(request: ChatHistoryRequest):
    """
    Process structured chat history (Q&A pairs) and store embeddings in Qdrant.
    """
    try:
        chat_history_dicts = [msg.dict() for msg in request.chat_history]
        
        result = process_and_embed_chat(
            user_id=request.user_id,
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
            user_id=request.user_id,
            full_chat_text=request.chat_text
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        return ChatResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {str(e)}")


@router.post("/next-question", response_model=NextQuestionResponse)
async def get_next_question(request: NextQuestionRequest):
    """
    Generate next personalized question using LLM based on chat history.
    
    - Questions 1-5: Focus on personality, values, relationship goals
    - Questions 6-10: Focus on social energy, lifestyle, activities
    - Send empty chat_history [] to get the first question
    - LLM generates contextual follow-ups based on previous answers
    - Automatically embeds and stores in Qdrant when 10 questions completed (requires user_id)
    """
    try:
        chat_history_dicts = [msg.dict() for msg in request.chat_history]
        
        result = generate_next_question(
            chat_history=chat_history_dicts,
            user_id=request.user_id
        )
        
        return NextQuestionResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate question: {str(e)}"
        )
