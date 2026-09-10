from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from app.core.auth import AuthUser, get_current_user
from app.core.llm_questionnaire import process_and_embed_chat, embed_full_chat, generate_next_question
from app.core.rate_limiter import rate_limiter

router = APIRouter(tags=["chat"])

# Ten questions per run; the cap allows retries without allowing a grind.
MAX_CHAT_HISTORY = 40
MAX_ANSWER_CHARS = 1000


class ChatMessage(BaseModel):
    q: str = Field(..., description="Question text", max_length=MAX_ANSWER_CHARS)
    a: str = Field(..., description="Answer text", max_length=MAX_ANSWER_CHARS)


class ChatHistoryRequest(BaseModel):
    chat_history: List[ChatMessage] = Field(
        ..., description="List of Q&A pairs", max_length=MAX_CHAT_HISTORY
    )


class FullChatRequest(BaseModel):
    chat_text: str = Field(
        ..., description="Full chat conversation as text", max_length=20_000
    )


class ChatResponse(BaseModel):
    status: str
    message: str
    user_email: Optional[str] = None
    answers_processed: Optional[int] = None


class NextQuestionRequest(BaseModel):
    # The user is taken from the session, never from the request body.
    chat_history: List[ChatMessage] = Field(
        default=[],
        description="List of previous Q&A pairs (empty array for first question)",
        max_length=MAX_CHAT_HISTORY,
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
def embed_chat_history(
    request: ChatHistoryRequest,
    caller: AuthUser = Depends(get_current_user),
):
    """
    Process structured chat history (Q&A pairs) and store embeddings in Qdrant.
    """
    try:
        chat_history_dicts = [msg.model_dump() for msg in request.chat_history]

        result = process_and_embed_chat(
            user_email=caller.email,
            chat_history=chat_history_dicts
        )

        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))

        return ChatResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {str(e)}")


@router.post("/embed-full-text", response_model=ChatResponse)
def embed_full_chat_text(
    request: FullChatRequest,
    caller: AuthUser = Depends(get_current_user),
):
    """
    Process full chat as single text string and store embeddings in Qdrant.
    """
    try:
        result = embed_full_chat(
            user_email=caller.email,
            full_chat_text=request.chat_text
        )

        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))

        return ChatResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {str(e)}")


@router.post("/next-question", response_model=NextQuestionResponse)
def get_next_question(
    request: NextQuestionRequest,
    caller: AuthUser = Depends(get_current_user),
):
    try:
        is_limited, seconds_until_reset = rate_limiter.is_rate_limited(
            key=f"chat:{caller.email}",
            max_requests=40,
            window_seconds=600
        )

        if is_limited:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Too many requests",
                    "message": f"Rate limit exceeded. Please try again in {seconds_until_reset} seconds.",
                    "retry_after": seconds_until_reset
                },
                headers={"Retry-After": str(seconds_until_reset)},
            )

        chat_history_dicts = [msg.model_dump() for msg in request.chat_history]

        result = generate_next_question(
            chat_history=chat_history_dicts,
            user_email=caller.email
        )

        return NextQuestionResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate question: {str(e)}"
        )
