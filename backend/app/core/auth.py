"""
EcoSnap — Auth Middleware
Validates Supabase JWT Bearer tokens via the Supabase REST Auth API (httpx).
100% compatible with Python 3.14 — no supabase-py SDK required.
"""
import logging
from typing import Any, Optional
from fastapi import Header, HTTPException
import httpx

from app.config import SUPABASE_URL, SUPABASE_SERVICE_KEY, supabase

logger = logging.getLogger(__name__)

SUPABASE_AUTH_URL = f"{SUPABASE_URL}/auth/v1/user" if SUPABASE_URL else ""


def _get_bearer_token(authorization: Optional[str]) -> str:
    """Extract Bearer token from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header format. Use: Bearer <token>")
    return parts[1].strip()


def get_current_user(authorization: Optional[str] = Header(None)) -> Any:
    """
    Validates a Supabase JWT token using the Supabase Auth REST API.
    Returns the user object dict on success.
    Raises HTTP 401 on any failure.
    """
    token = _get_bearer_token(authorization)

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                SUPABASE_AUTH_URL,
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": SUPABASE_SERVICE_KEY,
                },
            )
    except Exception as exc:
        logger.error(f"Auth API request failed: {exc}")
        raise HTTPException(status_code=401, detail="Auth service unavailable")

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = response.json()
    if not user or not user.get("id"):
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return user


def get_current_user_id(user: Any) -> str:
    """Extract user ID from the user dict returned by get_current_user."""
    user_id = None
    if isinstance(user, dict):
        user_id = user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Could not extract user ID from token")
    return user_id


def require_admin(user: Any) -> Any:
    """
    Checks that the authenticated user has is_admin = true in the profiles table.
    Raises HTTP 403 if not admin.
    """
    user_id = get_current_user_id(user)
    try:
        result = (
            supabase.table("profiles")
            .select("is_admin")
            .eq("id", user_id)
            .single()
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Admin check failed: {exc}")

    is_admin = False
    if isinstance(result.data, dict):
        is_admin = bool(result.data.get("is_admin"))

    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
