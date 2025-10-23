from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.llm_questionnaire import generate_next_question, store_user_answer

router = APIRouter()

@router.post("/{user_id}/next")
def next_question(user_id: int, db: Session = Depends(get_db)):
    return generate_next_question(db, user_id)

@router.post("/{user_id}/answer")
def submit_answer(user_id: int, answer: str, db: Session = Depends(get_db)):
    return store_user_answer(db, user_id, answer)