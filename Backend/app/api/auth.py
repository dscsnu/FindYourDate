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
    Frontend will handle the callback directly to maintain PKCE flow.
    """
    try:
        # Frontend will handle the callback directly
        final_redirect = redirect_to or f"{frontend_url}/auth/callback"
        
        response = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                # Redirect directly to frontend to preserve PKCE
                "redirect_to": final_redirect,
                "skip_browser_redirect": True
            }
        })

        return {
            "url": response.url
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate auth URL: {str(e)}")


@router.get('/google/callback')
async def google_callback(
    response: Response,
    code: Optional[str] = None,
    error: Optional[str] = None,
    redirect_to: Optional[str] = None
):
    """
    Handles the OAuth callback from Google.
    Exchanges the code for a session and stores tokens in httpOnly cookies.
    Tokens are NEVER exposed to frontend JavaScript.
    """
    if error:
        return RedirectResponse(url=f"{frontend_url}/?error={error}")
    
    if not code:
        return RedirectResponse(url=f"{frontend_url}/?error=missing_code")
    
    try:
        # Exchange code for session
        auth_response = supabase.auth.exchange_code_for_session({
            "auth_code": code
        })
        
        if not auth_response.session:
            return RedirectResponse(url=f"{frontend_url}/?error=auth_failed")
        
        # Create redirect response
        redirect_url = f"{frontend_url}/auth/callback?success=true"
        redirect_response = RedirectResponse(url=redirect_url)
        
        # Set httpOnly cookies (NOT accessible from JavaScript)
        # This keeps tokens secure and prevents XSS attacks
        redirect_response.set_cookie(
            key="access_token",
            value=auth_response.session.access_token,
            httponly=True,  # Cannot be accessed by JavaScript
            secure=False,   # Set to True in production with HTTPS
            samesite="lax", # CSRF protection
            max_age=auth_response.session.expires_in,
            path="/"
        )
        
        redirect_response.set_cookie(
            key="refresh_token",
            value=auth_response.session.refresh_token,
            httponly=True,
            secure=False,   # Set to True in production with HTTPS
            samesite="lax",
            max_age=60 * 60 * 24 * 30,  # 30 days
            path="/"
        )
        
        return redirect_response
        
    except Exception as e:
        return RedirectResponse(url=f"{frontend_url}/?error={str(e)}")


@router.post('/session/exchange')
async def exchange_session(callback_request: CallbackRequest, response: Response):
    """
    Exchange OAuth code for session tokens.
    Sets httpOnly cookies for security.
    Frontend uses this to complete the PKCE flow.
    """
    try:
        auth_response = supabase.auth.exchange_code_for_session({
            "auth_code": callback_request.code
        })
        
        if not auth_response.session:
            raise HTTPException(status_code=401, detail="Failed to exchange code for session")
        
        # Determine if we're in production
        is_production = frontend_url.startswith("https://")
        
        # Set httpOnly cookies for security
        response.set_cookie(
            key="access_token",
            value=auth_response.session.access_token,
            httponly=True,
            secure=is_production,
            samesite="none" if is_production else "lax",
            max_age=auth_response.session.expires_in,
            path="/"
        )
        
        response.set_cookie(
            key="refresh_token",
            value=auth_response.session.refresh_token,
            httponly=True,
            secure=is_production,
            samesite="none" if is_production else "lax",
            max_age=60 * 60 * 24 * 30,  # 30 days
            path="/"
        )
        
        return {
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            "expires_in": auth_response.session.expires_in,
            "expires_at": auth_response.session.expires_at,
            "token_type": auth_response.session.token_type,
            "user": {
                "id": auth_response.user.id,
                "email": auth_response.user.email,
                "user_metadata": auth_response.user.user_metadata,
                "app_metadata": auth_response.user.app_metadata,
                "created_at": auth_response.user.created_at
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Exchange error: {str(e)}")


@router.post('/refresh')
async def refresh_session(
    response: Response,
    refresh_token: Optional[str] = Cookie(None)
):
    """
    Refresh an expired session using refresh token from httpOnly cookie.
    """
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token found")
    
    try:
        auth_response = supabase.auth.refresh_session(refresh_token)

        if not auth_response.session:
            raise HTTPException(status_code=401, detail="Failed to refresh session")

        # Update cookies with new tokens
        response.set_cookie(
            key="access_token",
            value=auth_response.session.access_token,
            httponly=True,
            secure=False,  # Set to True in production
            samesite="lax",
            max_age=auth_response.session.expires_in,
            path="/"
        )
        
        response.set_cookie(
            key="refresh_token",
            value=auth_response.session.refresh_token,
            httponly=True,
            secure=False,  # Set to True in production
            samesite="lax",
            max_age=60 * 60 * 24 * 30,
            path="/"
        )

        return {"message": "Session refreshed successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Refresh error: {str(e)}")


@router.get('/user')
async def get_user(access_token: Optional[str] = Cookie(None)):
    """
    Get current user information using access token from httpOnly cookie.
    """
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
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
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


@router.post('/logout')
async def logout(
    response: Response,
    access_token: Optional[str] = Cookie(None)
):
    """
    Sign out user and clear httpOnly cookies.
    """
    try:
        if access_token:
            supabase.auth.sign_out(access_token)
        
        # Clear cookies
        response.delete_cookie(key="access_token", path="/")
        response.delete_cookie(key="refresh_token", path="/")
        
        return {"message": "Successfully logged out"}
    except Exception as e:
        # Still clear cookies even if Supabase signout fails
        response.delete_cookie(key="access_token", path="/")
        response.delete_cookie(key="refresh_token", path="/")
        return {"message": "Logged out (with errors)", "error": str(e)}
