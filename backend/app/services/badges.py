"""
EcoSnap — Badge Service
Evaluates and awards gamification badges based on report/upvote counts.
Uses the custom httpx SupabaseClient — no supabase-py SDK.
"""
import logging
from datetime import datetime, timezone

from app.config import supabase

logger = logging.getLogger(__name__)

BADGES = [
    {"id": "first_report",   "name": "First Report 🌱",   "icon": "seedling", "threshold": 1},
    {"id": "three_reports",  "name": "3 Reports 🔎",       "icon": "search",   "threshold": 3},
    {"id": "five_reports",   "name": "5 Reports 🌿",       "icon": "sprout",   "threshold": 5},
    {"id": "first_resolved", "name": "First Resolved 🏆",  "icon": "trophy",   "threshold": 1},
    {"id": "ten_upvotes",    "name": "10 Upvotes ⭐",      "icon": "star",     "threshold": 10},
]


def _get_user_badges(user_id: str) -> set[str]:
    try:
        result = supabase.table("user_badges").select("badge_id").eq("user_id", user_id).execute()
        return {row.get("badge_id") for row in (result.data or []) if row.get("badge_id")}
    except Exception as e:
        logger.warning(f"Badge fetch failed for {user_id}: {e}")
        return set()


def _insert_badges(user_id: str, badge_ids: list[str]) -> None:
    if not badge_ids:
        return
    now_iso = datetime.now(timezone.utc).isoformat()
    rows = [{"user_id": user_id, "badge_id": bid, "earned_at": now_iso} for bid in badge_ids]
    try:
        supabase.table("user_badges").insert(rows).execute()
        logger.info(f"Awarded badges to {user_id}: {badge_ids}")
    except Exception as e:
        logger.warning(f"Badge insert failed for {user_id}: {e}")


def _get_counts(user_id: str) -> dict:
    try:
        result = supabase.table("reports").select("id,status,upvotes").eq("user_id", user_id).execute()
        reports = result.data or []
        total_reports = len(reports)
        resolved_reports = len([r for r in reports if (r.get("status") or "").lower() == "resolved"])
        total_upvotes = sum(int(r.get("upvotes") or 0) for r in reports)
        return {"reports": total_reports, "resolved": resolved_reports, "upvotes": total_upvotes}
    except Exception as e:
        logger.warning(f"Count fetch failed for {user_id}: {e}")
        return {"reports": 0, "resolved": 0, "upvotes": 0}


def ensure_badges(user_id: str) -> list[str]:
    """Check thresholds and award any newly earned badges. Returns list of newly awarded badge IDs."""
    counts = _get_counts(user_id)
    earned = _get_user_badges(user_id)
    to_add = []

    if counts["reports"] >= 1 and "first_report" not in earned:
        to_add.append("first_report")
    if counts["reports"] >= 3 and "three_reports" not in earned:
        to_add.append("three_reports")
    if counts["reports"] >= 5 and "five_reports" not in earned:
        to_add.append("five_reports")
    if counts["resolved"] >= 1 and "first_resolved" not in earned:
        to_add.append("first_resolved")
    if counts["upvotes"] >= 10 and "ten_upvotes" not in earned:
        to_add.append("ten_upvotes")

    _insert_badges(user_id, to_add)
    return to_add


def get_badges_state(user_id: str) -> list[dict]:
    """Returns all badge definitions with earned=True/False for the given user."""
    earned = _get_user_badges(user_id)
    return [
        {
            "id": badge["id"],
            "name": badge["name"],
            "icon": badge["icon"],
            "earned": badge["id"] in earned,
        }
        for badge in BADGES
    ]
