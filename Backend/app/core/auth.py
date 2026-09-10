"""Request authentication. Every protected endpoint goes through get_current_user.

Identity always comes from the session cookie, never from a query parameter or
request body, so a caller cannot act on behalf of another email.
"""

import os
import threading
import time
from typing import Optional

from dotenv import load_dotenv
from fastapi import Cookie, HTTPException
from pydantic import BaseModel
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Empty means any domain. Set to e.g. "snu.edu.in" to restrict sign-in.
ALLOWED_EMAIL_DOMAINS = [
    d.strip().lower().lstrip("@")
    for d in os.getenv("ALLOWED_EMAIL_DOMAINS", "").split(",")
    if d.strip()
]

# Verifying a token is a network round trip to Supabase. Without a cache every
# authenticated request pays it, which is the difference between handling a
# crowd and falling over. Tokens are already short lived, so a small TTL is a
# safe trade.
_TOKEN_CACHE_TTL = int(os.getenv("AUTH_CACHE_TTL", "300"))
_TOKEN_CACHE_MAX = 10_000

_cache: dict[str, tuple[float, "AuthUser"]] = {}
_cache_lock = threading.Lock()


class AuthUser(BaseModel):
    id: str
    email: str
    name: Optional[str] = None


def email_allowed(email: str) -> bool:
    if not ALLOWED_EMAIL_DOMAINS:
        return True
    return email.lower().rsplit("@", 1)[-1] in ALLOWED_EMAIL_DOMAINS


def _cache_get(token: str) -> Optional["AuthUser"]:
    with _cache_lock:
        hit = _cache.get(token)
        if not hit:
            return None
        expires_at, user = hit
        if expires_at < time.monotonic():
            _cache.pop(token, None)
            return None
        return user


def _cache_put(token: str, user: "AuthUser") -> None:
    with _cache_lock:
        if len(_cache) >= _TOKEN_CACHE_MAX:
            now = time.monotonic()
            for k, (expires_at, _) in list(_cache.items()):
                if expires_at < now:
                    del _cache[k]
            if len(_cache) >= _TOKEN_CACHE_MAX:
                _cache.clear()
        _cache[token] = (time.monotonic() + _TOKEN_CACHE_TTL, user)


def forget_token(token: str) -> None:
    """Drop a cached verification, e.g. on logout."""
    with _cache_lock:
        _cache.pop(token, None)


def verify_token(token: str) -> AuthUser:
    cached = _cache_get(token)
    if cached:
        return cached

    try:
        response = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    if not response or not response.user or not response.user.email:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    user = AuthUser(
        id=str(response.user.id),
        email=response.user.email,
        name=(response.user.user_metadata or {}).get("full_name"),
    )

    if not email_allowed(user.email):
        raise HTTPException(
            status_code=403,
            detail=f"Sign in with your {ALLOWED_EMAIL_DOMAINS[0]} account",
        )

    _cache_put(token, user)
    return user


def get_current_user(access_token: Optional[str] = Cookie(None)) -> AuthUser:
    """FastAPI dependency: the authenticated caller, or 401."""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return verify_token(access_token)
