import os
from typing import Optional
from urllib.parse import quote

from dotenv import load_dotenv
from fastapi import APIRouter, Cookie, HTTPException, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.core.auth import (
    ALLOWED_EMAIL_DOMAINS,
    AuthUser,
    email_allowed,
    forget_token,
    get_current_user,
    supabase,
)

load_dotenv()

frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173").rstrip("/")
backend_url = os.environ.get("BACKEND_URL", "http://localhost:1386").rstrip("/")

# Cookies must carry Secure over HTTPS or the browser drops them; over plain
# http (local dev) Secure would drop them instead. Follow the frontend scheme.
COOKIE_SECURE = os.getenv(
    "COOKIE_SECURE", "true" if frontend_url.startswith("https://") else "false"
).lower() == "true"
# "lax" is fine while the API shares a registrable domain with the frontend.
# Put the API on an unrelated domain and this has to become "none".
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax").lower()
COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN") or None

REFRESH_MAX_AGE = 60 * 60 * 24 * 30

router = APIRouter(prefix="/auth", tags=["authentication"])


class CallbackRequest(BaseModel):
    code: str


def _set_session_cookies(response: Response, session) -> None:
    response.set_cookie(
        key="access_token",
        value=session.access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=session.expires_in,
        domain=COOKIE_DOMAIN,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=session.refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=REFRESH_MAX_AGE,
        domain=COOKIE_DOMAIN,
        path="/",
    )


def _clear_session_cookies(response: Response) -> None:
    for key in ("access_token", "refresh_token"):
        response.delete_cookie(key=key, path="/", domain=COOKIE_DOMAIN)


@router.get("/google/login")
def google_login(redirect_to: Optional[str] = None):
    """
    Initiates Google OAuth flow.
    Returns the OAuth URL that the frontend should redirect to.
    """
    try:
        # Routers are mounted under /api, so the callback lives there too.
        callback_url = f"{backend_url}/api/auth/google/callback"

        # Only ever hand Supabase our own frontend as the landing spot;
        # an attacker-supplied redirect_to would be an open redirect.
        final_redirect = f"{frontend_url}/auth/callback"

        options = {"redirect_to": callback_url}
        if ALLOWED_EMAIL_DOMAINS:
            # Hints Google's account chooser; the real check is server side.
            options["query_params"] = {"hd": ALLOWED_EMAIL_DOMAINS[0]}

        response = supabase.auth.sign_in_with_oauth(
            {"provider": "google", "options": options}
        )

        return {"url": response.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate auth URL: {str(e)}")


@router.get("/google/callback")
def google_callback(
    code: Optional[str] = None,
    error: Optional[str] = None,
):
    """
    Handles the OAuth callback from Google.
    Exchanges the code for a session and stores tokens in httpOnly cookies.
    Tokens are NEVER exposed to frontend JavaScript.
    """
    if error:
        return RedirectResponse(url=f"{frontend_url}/?error={quote(error)}")

    if not code:
        return RedirectResponse(url=f"{frontend_url}/?error=missing_code")

    try:
        auth_response = supabase.auth.exchange_code_for_session({"auth_code": code})
    except Exception:
        return RedirectResponse(url=f"{frontend_url}/?error=auth_failed")

    if not auth_response.session or not auth_response.user:
        return RedirectResponse(url=f"{frontend_url}/?error=auth_failed")

    if not email_allowed(auth_response.user.email or ""):
        return RedirectResponse(url=f"{frontend_url}/?error=domain_not_allowed")

    redirect_response = RedirectResponse(url=f"{frontend_url}/auth/callback?success=true")
    _set_session_cookies(redirect_response, auth_response.session)
    return redirect_response


@router.post("/refresh")
def refresh_session(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
):
    """
    Refresh an expired session using refresh token from httpOnly cookie.
    """
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token found")

    try:
        auth_response = supabase.auth.refresh_session(refresh_token)
    except Exception:
        _clear_session_cookies(response)
        raise HTTPException(status_code=401, detail="Failed to refresh session")

    if not auth_response.session:
        _clear_session_cookies(response)
        raise HTTPException(status_code=401, detail="Failed to refresh session")

    _set_session_cookies(response, auth_response.session)
    return {"message": "Session refreshed successfully"}


@router.get("/user")
def get_user(access_token: Optional[str] = Cookie(None)):
    """
    Get current user information using access token from httpOnly cookie.
    """
    user: AuthUser = get_current_user(access_token)
    return {"user": {"id": user.id, "email": user.email, "name": user.name}}


@router.post("/logout")
def logout(
    response: Response,
    access_token: Optional[str] = Cookie(None),
):
    """
    Sign out user and clear httpOnly cookies.
    """
    if access_token:
        forget_token(access_token)
        try:
            supabase.auth.sign_out(access_token)
        except Exception:
            pass  # The cookies still get cleared below.

    _clear_session_cookies(response)
    return {"message": "Successfully logged out"}
