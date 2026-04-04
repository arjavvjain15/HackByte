from typing import Any, Optional
from fastapi import Header, HTTPException
from app.core.supabase import get_supabase_client


def _get_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    return parts[1].strip()


def get_current_user(authorization: Optional[str] = Header(None)) -> Any:
    token = _get_bearer_token(authorization)
    client = get_supabase_client()
    try:
        result = client.auth.get_user(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}") from exc

    user = getattr(result, "user", None)
    if user is None and isinstance(result, dict):
        user = result.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


def get_current_user_id(user: Any) -> str:
    user_id = getattr(user, "id", None)
    if not user_id and isinstance(user, dict):
        user_id = user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")
    return user_id


def require_admin(user: Any) -> Any:
    user_id = get_current_user_id(user)
    client = get_supabase_client()
    try:
        result = client.table("profiles").select("is_admin").eq("id", user_id).single().execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Admin check failed: {exc}") from exc

    row = result.data if hasattr(result, "data") else None
    is_admin = False
    if isinstance(row, dict):
        is_admin = bool(row.get("is_admin"))
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
