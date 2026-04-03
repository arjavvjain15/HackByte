from fastapi import APIRouter, Depends
from typing import Any

from app.core.auth import get_current_user, get_current_user_id
from app.services.profiles import get_profile, get_dashboard, get_activity_feed

router = APIRouter(prefix="/api", tags=["profile"])


@router.get("/me/profile")
def my_profile_endpoint(
    user: Any = Depends(get_current_user),
):
    user_id = get_current_user_id(user)
    profile = get_profile(user_id)
    return {"profile": profile}


@router.get("/me/activity")
def my_activity_endpoint(
    user: Any = Depends(get_current_user),
):
    user_id = get_current_user_id(user)
    activity = get_activity_feed(user_id, limit=10)
    return {"activity": activity}


@router.get("/me/dashboard")
def my_dashboard_endpoint(
    user: Any = Depends(get_current_user),
):
    user_id = get_current_user_id(user)
    return get_dashboard(user_id)
