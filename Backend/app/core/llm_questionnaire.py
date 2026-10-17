import logging
from typing import List, Dict

import numpy as np
from fastapi import HTTPException

from app.core.llm import client, llm_slot
from app.db.qdrant_client import store_embedding
from app.utils.embeddings import get_text_embedding

logger = logging.getLogger(__name__)

# (topic, base question) per slot. The base question doubles as the fallback when the LLM fails.
QUESTION_TOPICS = [
    ("first impression", "What's something about you that people usually notice first?"),
    ("how friends see them", "How would your friends describe you in three words?"),
    ("little joys", "What's a small thing that makes your day better?"),
    ("meeting new people", "How do you usually break the ice when you meet someone new?"),
    ("trying new things", "What's something you'd love to try this year?"),
    ("ideal free day", "How do you like to spend a free Saturday?"),
    ("social energy", "At a party, are you usually on the dance floor, chatting with friends, or somewhere quieter?"),
    ("music taste", "What's a song you'd love to hear at prom, and why?"),
    ("current favourites", "What show, movie or game are you into right now?"),
    ("hobby or skill", "What's a hobby or skill you're proud of?"),
]


def process_and_embed_chat(user_email: str, chat_history: List[Dict[str, str]]):
    if not chat_history or len(chat_history) == 0:
        return {"status": "error", "message": "Chat history is empty"}
    
    personality_answers = []
    social_answers = []
    
    for idx, entry in enumerate(chat_history):
        answer = entry.get("a", "")
        if answer:
            if idx < 5:
                personality_answers.append(answer)
            else:
                social_answers.append(answer)
    
    personality_text = " ".join(personality_answers) if personality_answers else ""
    social_text = " ".join(social_answers) if social_answers else ""
    
    personality_vec = get_text_embedding(personality_text) if personality_text else []
    social_vec = get_text_embedding(social_text) if social_text else []
    
    if personality_vec and social_vec:
        final_vec = np.mean([personality_vec, social_vec], axis=0)
    elif personality_vec:
        final_vec = np.array(personality_vec)
    elif social_vec:
        final_vec = np.array(social_vec)
    else:
        return {"status": "error", "message": "No valid answers to embed"}
    
    store_embedding(vector=final_vec, user_email=user_email)
    
    return {
        "status": "success",
        "message": "Chat embedded and stored successfully",
        "user_email": user_email,
        "answers_processed": len(personality_answers) + len(social_answers)
    }


def embed_full_chat(user_email: str, full_chat_text: str):
    if not full_chat_text or len(full_chat_text.strip()) == 0:
        return {"status": "error", "message": "Chat text is empty"}
    
    chat_vector = get_text_embedding(full_chat_text)
    
    if not chat_vector:
        return {"status": "error", "message": "Failed to generate embedding"}
    
    final_vec = np.array(chat_vector)
    store_embedding(vector=final_vec, user_email=user_email)
    
    return {
        "status": "success",
        "message": "Chat embedded and stored successfully",
        "user_email": user_email
    }


def generate_next_question(chat_history: List[Dict[str, str]], user_email: str = None) -> Dict:
    current_count = len(chat_history)
    
    # Determine if questionnaire is complete
    if current_count >= 10:
        # Auto-embed if user_email provided
        embedding_result = None
        if user_email:
            try:
                embedding_result = process_and_embed_chat(user_email, chat_history)
            except HTTPException:
                # Queue was full. Surface it so the client retries and the
                # profile actually gets embedded; there is no manual path.
                raise
            except Exception as e:
                logger.exception("Embedding failed for %s", user_email)
                return {
                    "question": None,
                    "is_complete": True,
                    "question_number": current_count,
                    "total_questions": 10,
                    "message": "Questionnaire complete but embedding failed. Please try manually.",
                    "embedding_error": str(e)
                }
        
        response = {
            "question": None,
            "is_complete": True,
            "question_number": current_count,
            "total_questions": 10,
            "message": "Questionnaire complete! Profile created and ready to find matches."
        }
        
        # Add embedding status
        if embedding_result:
            if embedding_result.get("status") == "success":
                response["embedding_status"] = "success"
                response["user_email"] = embedding_result.get("user_email")
                response["answers_processed"] = embedding_result.get("answers_processed")
            else:
                response["embedding_status"] = "error"
                response["embedding_error"] = embedding_result.get("message")
        
        return response
    
    # Every user answers the same topic per slot so their embeddings stay comparable;
    # the LLM only rephrases. Slots 0-4 are personality, 5-9 social (see process_and_embed_chat).
    category = "personality" if current_count < 5 else "social_energy"
    topic, base_question = QUESTION_TOPICS[current_count]

    system_prompt = """You write questions for a friendly prom-date matching form for high school/college students. You ask ONE simple question at a time.

        Every user gets the SAME topic for each question number, so answers can be compared fairly for matching.

        CRITICAL RULES:
        - Return ONLY the question - NO introductions like "Sure, here's", "Here is", "Great answer!", etc.
        - The question MUST ask the same thing as the base question - only lightly vary the wording, or keep it as is
        - Tone: warm, polite and simple, like a friendly classmate or event organiser - subtle, not over the top
        - No slang, nicknames, jokes about the person, flirting or exaggerated words (avoid "quirky", "wild", "crazy", "weird", "screams", "mischief", "cringe", "chaos", "legend")
        - Never refer to their earlier answers
        - Keep it SHORT (under 20 words)
        - Ask for an answer in words (no "answer in emojis" or yes/no questions)
        - Keep content appropriate for ages 16+ - nothing sexual, romantic-pressure, personal or controversial"""

    user_prompt = f"""Question #{current_count + 1} of 10.
Topic: {topic}
Base question: {base_question}

Return ONLY the question text."""

    try:
        # Call OpenAI API
        with llm_slot():
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.4,
                max_tokens=150
            )

        question = response.choices[0].message.content.strip()
        
        # Remove quotes if LLM added them
        if question.startswith('"') and question.endswith('"'):
            question = question[1:-1]
        if question.startswith("'") and question.endswith("'"):
            question = question[1:-1]
        
        return {
            "question": question,
            "is_complete": False,
            "question_number": current_count + 1,
            "total_questions": 10,
            "category": category
        }
    
    except HTTPException:
        # Queue was full; let the client back off rather than silently
        # handing everyone the same canned questions during a rush.
        raise
    except Exception:
        # Fallback questions if LLM fails
        logger.exception("LLM question generation failed, using fallback")
        return {
            "question": base_question,
            "is_complete": False,
            "question_number": current_count + 1,
            "total_questions": 10,
            "category": category,
            "note": "Using fallback question due to LLM error"
        }