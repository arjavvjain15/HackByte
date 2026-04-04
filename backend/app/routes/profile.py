"""
EcoSnap — Profile Routes
GET /api/me/profile    — Current user's profile
GET /api/me/dashboard  — Full dashboard bundle (profile + stats + reports + badges + activity)
GET /api/me/activity   — Recent activity feed
GET /api/me/badges     — Badge states (earned / locked)
"""
import logging
from fastapi import APIRouter, Depends
from typing import Any

from app.core.auth import get_current_user, get_current_user_id
from app.services.profiles import get_profile, get_dashboard, get_activity_feed
from app.services.badges import get_badges_state

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Profile"])


@router.get("/me/profile")
def my_profile_endpoint(user: Any = Depends(get_current_user)):
    """Returns the current user's profile row."""
    user_id = get_current_user_id(user)
    profile = get_profile(user_id)
    return {"profile": profile}


@router.get("/me/dashboard")
def my_dashboard_endpoint(user: Any = Depends(get_current_user)):
    """
    Full dashboard bundle for the user PWA:
    - profile
    - stats (reports_filed, issues_resolved, upvotes_given)
    - my_reports (with progress_percent and status_label)
    - activity (recent status changes)
    - badges (earned / locked state for all 5 badges)
    """
    user_id = get_current_user_id(user)
    return get_dashboard(user_id)


@router.get("/me/activity")
def my_activity_endpoint(user: Any = Depends(get_current_user)):
    """Recent activity: report status changes + upvoted escalations."""
    user_id = get_current_user_id(user)
    activity = get_activity_feed(user_id, limit=15)
    return {"activity": activity}


@router.get("/me/badges")
def my_badges_endpoint(user: Any = Depends(get_current_user)):
    """All badge definitions with earned=true/false for the current user."""
    user_id = get_current_user_id(user)
    badges = get_badges_state(user_id)
    return {"badges": badges}
