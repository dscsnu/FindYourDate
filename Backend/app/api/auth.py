import os
from supabase import create_client
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Response, Cookie, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")

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


class CallbackRequest(BaseModel):
    code: str


@router.get('/google/login')
async def google_login(redirect_to: Optional[str] = None):
    """
    Initiates Google OAuth flow.
    Returns the OAuth URL that the frontend should redirect to.
    """
    try:
        callback_url = f"{os.environ.get('BACKEND_URL', 'http://localhost:8000')}/auth/google/callback"
        
        response = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": callback_url,
                "query_params": {
                    "redirect_to": redirect_to or f"{frontend_url}/userForm"
                }
            }
        })

        return {
            "url": response.url
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate auth URL: {str(e)}")


@router.get('/google/callback')
async def google_callback(
    request: Request,
    code: Optional[str] = None,
    error: Optional[str] = None,
    redirect_to: Optional[str] = None
):
    """
    Handles the OAuth callback from Google.
    Exchanges the code for a session and redirects to frontend with session data.
    """
    if error:
        return RedirectResponse(url=f"{frontend_url}?error={error}")
    
    if not code:
        return RedirectResponse(url=f"{frontend_url}?error=missing_code")
    
    try:
        # Exchange code for session
        response = supabase.auth.exchange_code_for_session({
            "auth_code": code
        })
        
        if not response.session:
            return RedirectResponse(url=f"{frontend_url}?error=auth_failed")
        
        # Create redirect URL with session data as URL parameters (temporary, will be stored in frontend)
        redirect_url = redirect_to or f"{frontend_url}/userForm"
        
        # Add session tokens as query params (frontend will store these securely)
        redirect_url += f"?access_token={response.session.access_token}"
        redirect_url += f"&refresh_token={response.session.refresh_token}"
        redirect_url += f"&expires_at={response.session.expires_at}"
        
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        return RedirectResponse(url=f"{frontend_url}?error={str(e)}")


@router.post('/session/exchange')
async def exchange_session(callback_request: CallbackRequest):
    """
    Exchange OAuth code for session tokens.
    Used when frontend handles the callback directly.
    """
    try:
        response = supabase.auth.exchange_code_for_session({
            "auth_code": callback_request.code
        })
        
        if not response.session:
            raise HTTPException(status_code=401, detail="Failed to exchange code for session")
        
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
        raise HTTPException(status_code=400, detail=f"Exchange error: {str(e)}")


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
