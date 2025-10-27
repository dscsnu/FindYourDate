from fastapi import APIRouter, HTTPException, Depends, Cookie
from sqlalchemy.orm import Session
from typing import Optional
from supabase import create_client
import os
from app.models.user_model import User
from app.db.database import SessionLocal
from app.db.qdrant_client import qdrant, get_embedding

router = APIRouter(tags=["status"])

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase = create_client(url, key)

def get_db():
    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="Database is not available")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def verify_auth(access_token: Optional[str] = Cookie(None)):
    """Verify authentication using httpOnly cookie"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Verify token with Supabase
        user_response = supabase.auth.get_user(access_token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_response.user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


@router.get("/user-status")
async def check_user_status(
    email: str,
    db: Session = Depends(get_db),
    user = Depends(verify_auth)
):
    """
    Check user's status and determine where they should be redirected.
    
    Returns:
    - exists_in_db: bool - Whether user exists in database
    - has_embedding: bool - Whether user has embedding in Qdrant
    - redirect_to: str - Where to redirect: "form", "chat", or "complete"
    - user_id: int (optional) - User ID if exists in database
    """
    
    # Check if user exists in database
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # User doesn't exist in DB - needs to fill form
        return {
            "exists_in_db": False,
            "has_embedding": False,
            "redirect_to": "form",
            "user_id": None
        }
    
    # User exists, now check if they have embedding in Qdrant
    try:
        # Try to get user's embedding by email
        embedding = get_embedding(user.email)
        
        has_embedding = embedding is not None
        
        if not has_embedding:
            # User exists but no embedding - needs to chat
            return {
                "exists_in_db": True,
                "has_embedding": False,
                "redirect_to": "chat",
                "user_id": user.id
            }
        else:
            # User exists and has embedding - matching complete
            return {
                "exists_in_db": True,
                "has_embedding": True,
                "redirect_to": "complete",
                "user_id": user.id
            }
            
    except Exception as e:
        # If Qdrant check fails, assume no embedding and send to chat
        return {
            "exists_in_db": True,
            "has_embedding": False,
            "redirect_to": "chat",
            "user_id": user.id,
            "qdrant_error": str(e)
        }
