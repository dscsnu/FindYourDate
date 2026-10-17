import logging
from typing import List, Dict

import numpy as np
from fastapi import HTTPException

from app.core.llm import client, llm_slot
from app.db.qdrant_client import store_embedding
from app.utils.embeddings import get_text_embedding

logger = logging.getLogger(__name__)


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
    
    # Determine category based on question number
    if current_count < 5:
        category = "personality"
        category_description = "personality, quirks, sense of humour, little joys, how they act around people"
    else:
        category = "social_energy"
        category_description = "social life, weekends, parties, music, hobbies, energy levels"
    
    # Build conversation context for LLM
    conversation_context = ""
    if chat_history:
        conversation_context = "Previous conversation:\n"
        for i, entry in enumerate(chat_history, 1):
            conversation_context += f"Q{i}: {entry.get('q', '')}\nA{i}: {entry.get('a', '')}\n\n"
    
    # Create LLM prompt
    if current_count == 0:
        # First question
        system_prompt = """You are the fun, slightly cheeky host of a prom-date matchmaking quiz for high school/college students. Ask ONE light, playful question that reveals their personality.

        CRITICAL RULES:
        - Return ONLY the question - NO introductions like "Sure, here's", "Here is", etc.
        - It's for finding a prom date, so keep it fun and low-stakes - never deep, heavy or interview-like
        - Avoid serious topics: life goals, values, conflict, ideal relationships, career
        - Keep it SHORT (under 20 words), casual, like a friend asking at a party
        - Ask for an answer in words (no "answer in emojis" or one-word/yes-no questions)
        - Keep content appropriate for ages 16+ (PG-16), nothing sexual

        Examples of the right vibe:
        - What's the most 'you' thing you've ever done?
        - If your friends had to describe you in three words, what would they say?
        - What's a small thing that instantly makes your day better?"""

        user_prompt = "Ask the first fun question about their personality. Just the question, nothing else."

    else:
        # Follow-up questions
        system_prompt = f"""You are the fun, slightly cheeky host of a prom-date matchmaking quiz for high school/college students. Ask ONE light, playful, personalized question.

        Current focus: {category_description}

        CRITICAL RULES:
        - Return ONLY the question - NO introductions like "Sure, here's", "Here is", "Great answer!", etc.
        - It's for finding a prom date, so keep it fun and low-stakes - never deep, heavy or interview-like
        - Avoid serious topics: life goals, values, conflict, ideal relationships, career
        - Keep it SHORT (under 25 words), casual, like a friend asking at a party
        - Ask for an answer in words (no "answer in emojis" or yes/no questions)
        - Keep content appropriate - avoid sexual/controversial topics, divert topic in case
        - About half the time, pick up a specific detail from one of their earlier answers and spin a new, playful question off it (e.g. they mentioned biryani -> "Would you cook biryani for your prom date, or would you rather be fed?")
        - For personality (1-5): quirks, humour, little joys, how they act around people
        - For social (6-10): weekends, parties, music, current obsessions, hobbies, energy levels
        - Every question must cover a NEW topic - never repeat a theme already asked (e.g. only ONE question about making people laugh, only ONE about parties)

        Examples of the right vibe:
        - What's your go-to move when a conversation gets awkward?
        - At a party, where would we find you: dance floor, snack table, or deep in conversation?
        - What song would you request at prom, and why?
        - What's your current obsession: a show, game, food, anything?
        """
        
        user_prompt = f"""Generate question #{current_count + 1} about {category_description}.

{conversation_context}

Return ONLY the question text - no greetings, no introductions, just the question."""
    
    try:
        # Call OpenAI API
        with llm_slot():
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
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
        fallback_questions = {
            0: "What's the most 'you' thing you've ever done?",
            1: "If your friends had to describe you in three words, what would they say?",
            2: "What's a small thing that instantly makes your day better?",
            3: "What's your go-to move when a conversation gets awkward?",
            4: "What's something on your bucket list you'd actually do this year?",
            5: "What's your ideal way to spend a free Saturday?",
            6: "At a party, where would we find you: dance floor, snack table, or deep in conversation?",
            7: "What song would you request at prom, and why?",
            8: "What's your current obsession: a show, game, food, anything?",
            9: "What's a hobby or skill you'd love to show off to your date?"
        }
        
        return {
            "question": fallback_questions.get(current_count, "Tell me more about yourself."),
            "is_complete": False,
            "question_number": current_count + 1,
            "total_questions": 10,
            "category": category,
            "note": "Using fallback question due to LLM error"
        }