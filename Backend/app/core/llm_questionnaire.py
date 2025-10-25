import os
from openai import OpenAI
from app.db.qdrant_client import store_embedding
from app.utils.embeddings import get_text_embedding
import numpy as np
from typing import List, Dict

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def process_and_embed_chat(user_id: int, chat_history: List[Dict[str, str]]):
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
    
    store_embedding(vector=final_vec, user_id=user_id)
    
    return {
        "status": "success",
        "message": "Chat embedded and stored successfully",
        "user_id": user_id,
        "answers_processed": len(personality_answers) + len(social_answers)
    }


def embed_full_chat(user_id: int, full_chat_text: str):
    if not full_chat_text or len(full_chat_text.strip()) == 0:
        return {"status": "error", "message": "Chat text is empty"}
    
    chat_vector = get_text_embedding(full_chat_text)
    
    if not chat_vector:
        return {"status": "error", "message": "Failed to generate embedding"}
    
    final_vec = np.array(chat_vector)
    store_embedding(vector=final_vec, user_id=user_id)
    
    return {
        "status": "success",
        "message": "Chat embedded and stored successfully",
        "user_id": user_id
    }


def generate_next_question(chat_history: List[Dict[str, str]], user_id: int = None) -> Dict:
    current_count = len(chat_history)
    
    # Determine if questionnaire is complete
    if current_count >= 10:
        # Auto-embed if user_id provided
        embedding_result = None
        if user_id:
            try:
                embedding_result = process_and_embed_chat(user_id, chat_history)
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
                response["user_id"] = embedding_result.get("user_id")
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
        system_prompt = """You are a dating app questionnaire assistant. Generate an engaging, friendly first question 
        about the user's personality and values. Keep it open-ended but specific. Make it feel natural and conversational.
        Focus on: personality, core values, what matters most to them in life."""
        
        user_prompt = "Generate the first question for a new user on a dating app. Make it about their core personality or values."
    
    else:
        # Follow-up questions
        system_prompt = f"""You are a dating app questionnaire assistant. Generate personalized follow-up questions 
        based on the user's previous answers. The questions will be used to create embeddings for matching via cosine similarity.

        Current focus area: {category_description}
        
        Rules:
        - Ask ONE clear, specific question
        - Make it conversational and natural
        - Build on their previous answers when relevant
        - Keep questions focused on the current category
        - Avoid yes/no questions - encourage detailed responses
        - For personality questions (1-5): Focus on values, emotional traits, relationship expectations, communication style
        - For social questions (6-10): Focus on activities, energy levels, social preferences, lifestyle, hobbies
        """
        
        user_prompt = f"""Based on this conversation, generate question #{current_count + 1} focused on {category_description}.

{conversation_context}

Generate a personalized follow-up question that:
1. Builds naturally from their previous answers
2. Focuses on {category_description}
3. Helps understand their compatibility with potential matches
4. Encourages them to share meaningful details

Return ONLY the question text, nothing else."""
    
    try:
        # Call OpenAI API
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