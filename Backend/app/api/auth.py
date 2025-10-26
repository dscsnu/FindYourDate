import os
from supabase import create_client
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

supabase = create_client(url, key)
router = APIRouter(prefix='/auth', tags=["authentication"])


class GoogleAuthRequest(BaseModel):
    id_token: str


class SessionResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    expires_at: int
    token_type: str
    user: dict


@router.post('/google', response_model=SessionResponse)
async def google_auth(auth_request: GoogleAuthRequest):
    """
    Authenticate user with Google ID token from frontend.
    Returns session data (access_token, refresh_token, user info) for frontend to store.
    """
    try:
        # Sign in with Google ID token
        response = supabase.auth.sign_in_with_id_token({
            "provider": "google",
            "token": auth_request.id_token
        })

        if not response.session:
            raise HTTPException(status_code=401, detail="Authentication failed")

        # Return session data for frontend to store
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "expires_in": response.session.expires_in,
            "expires_at": response.session.expires_at,
            "token_type": response.session.token_type,
            "user": {
                "id": response.user.id,
                "email": response.user.email,
                "user_metadata": response.user.user_metadata,
                "app_metadata": response.user.app_metadata,
                "created_at": response.user.created_at
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication error: {str(e)}")


@router.get('/google/url')
async def get_google_auth_url(redirect_to: Optional[str] = None):
    """
    Get Google OAuth URL for client-side redirect.
    The frontend can redirect users to this URL to start the OAuth flow.
    """
    try:
        response = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": redirect_to or f"{os.environ.get('FRONTEND_URL', 'http://localhost:5173')}/auth/callback"
            }
        })

        return {
            "url": response.url
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate auth URL: {str(e)}")


@router.post('/refresh')
async def refresh_session(refresh_token: str):
    """
    Refresh an expired session using refresh token.
    """
    try:
        response = supabase.auth.refresh_session(refresh_token)

        if not response.session:
            raise HTTPException(status_code=401, detail="Failed to refresh session")

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "expires_in": response.session.expires_in,
            "expires_at": response.session.expires_at,
            "token_type": response.session.token_type
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Refresh error: {str(e)}")


@router.get('/user')
async def get_user(access_token: str):
    """
    Get current user information using access token.
    """
    try:
        response = supabase.auth.get_user(access_token)

        if not response.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        return {
            "user": {
                "id": response.user.id,
                "email": response.user.email,
                "user_metadata": response.user.user_metadata,
                "app_metadata": response.user.app_metadata,
                "created_at": response.user.created_at
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get user: {str(e)}")


@router.post('/logout')
async def logout(access_token: str):
    """
    Sign out user and invalidate their session.
    """
    try:
        supabase.auth.sign_out(access_token)
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Logout error: {str(e)}")
