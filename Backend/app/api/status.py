from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import AuthUser, get_current_user
from app.db.database import get_db
from app.db.qdrant_client import get_embedding
from app.models.user_model import User

router = APIRouter(tags=["status"])


@router.get("/user-status")
def check_user_status(
    caller: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Check the signed-in user's status and where they should be redirected.

    Returns:
    - exists_in_db: bool - Whether user exists in database
    - has_embedding: bool - Whether user has embedding in Qdrant
    - redirect_to: str - Where to redirect: "form", "chat", or "complete"
    - user_id: int (optional) - User ID if exists in database
    """

    user = db.query(User).filter(User.email == caller.email).first()

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
