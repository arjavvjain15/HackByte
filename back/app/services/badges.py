from datetime import datetime, timezone
from fastapi import HTTPException

from app.core.supabase import get_supabase_client

BADGES = [
    {"id": "first_report", "name": "First Report", "icon": "seedling", "threshold": 1},
    {"id": "three_reports", "name": "3 Reports", "icon": "search", "threshold": 3},
    {"id": "five_reports", "name": "5 Reports", "icon": "sprout", "threshold": 5},
    {"id": "first_resolved", "name": "First Resolved", "icon": "trophy", "threshold": 1},
    {"id": "ten_upvotes", "name": "10 Upvotes", "icon": "star", "threshold": 10},
]


def _get_user_badges(user_id: str) -> set[str]:
    client = get_supabase_client()
    try:
        result = client.table("user_badges").select("badge_id").eq("user_id", user_id).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Badge fetch failed: {exc}") from exc
    return {row.get("badge_id") for row in (result.data or []) if row.get("badge_id")}


def _insert_badges(user_id: str, badge_ids: list[str]) -> None:
    if not badge_ids:
        return
    client = get_supabase_client()
    now_iso = datetime.now(timezone.utc).isoformat()
    rows = [{"user_id": user_id, "badge_id": bid, "earned_at": now_iso} for bid in badge_ids]
    try:
        client.table("user_badges").insert(rows).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Badge insert failed: {exc}") from exc


def _get_counts(user_id: str) -> dict:
    client = get_supabase_client()
    try:
        reports_res = client.table("reports").select("id,status,upvotes").eq("user_id", user_id).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Report count failed: {exc}") from exc
    reports = reports_res.data or []
    total_reports = len(reports)
    resolved_reports = len([r for r in reports if (r.get("status") or "").lower() == "resolved"])
    total_upvotes = sum(int(r.get("upvotes") or 0) for r in reports)
    return {
        "reports": total_reports,
        "resolved": resolved_reports,
        "upvotes": total_upvotes,
    }


def ensure_badges(user_id: str) -> list[str]:
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
    earned = _get_user_badges(user_id)
    state = []
    for badge in BADGES:
        state.append(
            {
                "id": badge["id"],
                "name": badge["name"],
                "icon": badge["icon"],
                "earned": badge["id"] in earned,
            }
        )
    return state
