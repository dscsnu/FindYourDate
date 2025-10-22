import os
from openai import OpenAI
from sqlalchemy.orm import Session
from models import ChatSession, User
from app.db.qdrant_client import store_embedding
from app.utils.embeddings import get_text_embedding
import numpy as np

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_or_create_session(session: Session, user_id: int) -> ChatSession:
    chat = session.query(ChatSession).filter(ChatSession.user_id == user_id).first()
    if not chat:
        chat = ChatSession(user_id=user_id, phase="personality", step=0, history=[])
        session.add(chat)
        session.commit()
    return chat


def generate_next_question(session: Session, user_id: int):
    chat = get_or_create_session(session, user_id)
    step = chat.step
    phase = chat.phase

    if step < 5:
        phase = "personality"
    elif step < 10:
        phase = "social"
        chat.phase = "social"
        session.commit()
    else:
        finalize_user_embeddings(session, user_id)
        return {"done": True, "message": "All 10 questions completed. Compatibility profile generated."}

    history_text = ""
    for idx, entry in enumerate(chat.history):
        history_text += f"Q{idx+1}: {entry['q']}\nA{idx+1}: {entry.get('a', '')}\n"

    prompt = f"""
    You are a compatibility interviewer.
    Generate ONE open-ended question for phase '{phase}'.

    Guidelines:
    - If 'personality': explore emotional values, empathy, communication, conflict style, and personal growth.
    - If 'social': explore social energy, independence, attachment, and lifestyle alignment.
    - Keep the question conversational and natural.
    - Avoid yes/no phrasing and avoid repeating past topics.

    Conversation so far:
    {history_text or 'No history yet.'}
    """

    res = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": "You are a friendly interviewer exploring romantic compatibility."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=80
    )

    question = res.choices[0].message.content.strip()

    chat.history.append({"q": question})
    chat.last_question = question
    chat.step += 1
    session.commit()

    return {"question": question, "phase": phase, "step": chat.step}

def store_user_answer(session: Session, user_id: int, answer: str):
    chat = get_or_create_session(session, user_id)

    if chat.history and "a" not in chat.history[-1]:
        chat.history[-1]["a"] = answer
        chat.last_question = None
        session.commit()
        return {"status": "saved", "step": chat.step}
    return {"status": "no_pending_question"}


def get_chat_history(session: Session, user_id: int):
    chat = get_or_create_session(session, user_id)
    return {
        "phase": chat.phase,
        "step": chat.step,
        "history": chat.history
    }


def finalize_user_embeddings(session: Session, user_id: int):
    chat = session.query(ChatSession).filter(ChatSession.user_id == user_id).first()
    user = session.query(User).filter(User.id == user_id).first()
    if not chat or not user:
        return None

    personality_answers = [entry["a"] for i, entry in enumerate(chat.history[:5]) if entry.get("a")]
    social_answers = [entry["a"] for i, entry in enumerate(chat.history[5:]) if entry.get("a")]

    personality_text = " ".join(personality_answers)
    social_text = " ".join(social_answers)

    personality_vec = get_text_embedding(personality_text)
    social_vec = get_text_embedding(social_text)

    final_vec = np.mean([personality_vec, social_vec], axis=0).tolist()

    store_embedding(vector=final_vec, user_id=user.id)

    user.preferences = {"personality_vector": personality_vec, "social_vector": social_vec}
    session.commit()

    return {"status": "embedded", "user_id": user.id}