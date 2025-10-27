import os
from openai import OpenAI
from app.db.qdrant_client import store_embedding
from app.utils.embeddings import get_text_embedding
import numpy as np
from typing import List, Dict

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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
            except Exception as e:
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
        category_description = "personality, core values, relationship goals, emotional traits, life priorities"
    else:
        category = "social_energy"
        category_description = "social activities, lifestyle preferences, energy levels, hobbies, how they spend time"
    
    # Build conversation context for LLM
    conversation_context = ""
    if chat_history:
        conversation_context = "Previous conversation:\n"
        for i, entry in enumerate(chat_history, 1):
            conversation_context += f"Q{i}: {entry.get('q', '')}\nA{i}: {entry.get('a', '')}\n\n"
    
    # Create LLM prompt
    if current_count == 0:
        # First question
        system_prompt = """You are a dating app questionnaire assistant for high school/college students. Generate a SHORT, friendly question about personality and values. 
        
        CRITICAL RULES:
        - Return ONLY the question - NO introductions like "Sure, here's", "Here is", etc.
        - Keep questions SHORT (under 15 words)
        - Keep content appropriate for ages 16+ (PG-16)
        - Make it casual and natural
        - Avoid anything sexual"""
        
        user_prompt = "Generate a short first question about their personality or values. Just the question, nothing else."
    
    else:
        # Follow-up questions
        system_prompt = f"""You are a dating app questionnaire assistant for high school/college students. Generate SHORT, personalized questions.

        Current focus: {category_description}
        
        CRITICAL RULES:
        - Return ONLY the question - NO introductions like "Sure, here's", "Here is", "Great answer!", etc.
        - Keep questions SHORT (under 40 words)
        - Keep content appropriate - avoid sexual/controversial topics, divert topic in case
        - Try to build on their previous answers(but its not necessary) and on the context(personality/social) naturally
        - Avoid yes/no questions
        - For personality (1-5): values, traits, communication, goals
        - For social (6-10): activities, hobbies, lifestyle, energy levels
        - Dont ask repetitive questions, explore more areas, even if its not related to previous answers
        - DO NOT ASK SIMILAR QUESTIONS, EXPLORE DIFFERENT ASPECTS OF THEIR PERSONALITY AND LIFESTYLE
        """
        
        user_prompt = f"""Generate question #{current_count + 1} about {category_description}.

{conversation_context}

Return ONLY the question text - no greetings, no introductions, just the question."""
    
    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-5-mini",
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
    
    except Exception as e:
        # Fallback questions if LLM fails
        fallback_questions = {
            0: "What are the most important values you look for in a partner?",
            1: "How would your closest friends describe your personality?",
            2: "What does your ideal relationship look like?",
            3: "How do you typically handle disagreements or conflicts?",
            4: "What are your long-term goals in life and love?",
            5: "How do you like to spend your free time?",
            6: "Are you more of an introvert, extrovert, or somewhere in between?",
            7: "What kind of activities energize you the most?",
            8: "Describe your perfect weekend.",
            9: "What hobbies or interests are you passionate about?"
        }
        
        return {
            "question": fallback_questions.get(current_count, "Tell me more about yourself."),
            "is_complete": False,
            "question_number": current_count + 1,
            "total_questions": 10,
            "category": category,
            "note": "Using fallback question due to LLM error"
        }