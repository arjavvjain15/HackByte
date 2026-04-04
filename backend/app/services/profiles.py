"""
EcoSnap — Profile Service
User profile, dashboard bundle, activity feed.
Uses custom httpx SupabaseClient — no supabase-py SDK.
"""
import logging
from datetime import datetime
from fastapi import HTTPException

from app.config import supabase
from app.services.badges import get_badges_state

logger = logging.getLogger(__name__)


def _short_id(report_id: str) -> str:
    if not report_id:
        return ""
    return report_id.split("-")[-1][:4]


def get_profile(user_id: str) -> dict:
    """Fetch a user's profile row from the profiles table."""
    try:
        result = (
            supabase.table("profiles")
            .select("id,display_name,avatar_url,is_admin,reports_submitted,reports_resolved,created_at")
            .eq("id", user_id)
            .single()
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Profile not found: {exc}")

    if not isinstance(result.data, dict):
        raise HTTPException(status_code=404, detail="Profile not found")
    return result.data


def get_upvotes_given_count(user_id: str) -> int:
    """Count how many upvotes this user has cast."""
    try:
        result = supabase.table("upvotes").select("id").eq("user_id", user_id).execute()
        return len(result.data or [])
    except Exception as e:
        logger.warning(f"Upvotes given count failed: {e}")
        return 0


def get_user_reports(user_id: str) -> list[dict]:
    """Fetch all reports by this user with progress percent and status label added."""
    try:
        result = (
            supabase.table("reports")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Reports fetch failed: {exc}")

    rows = result.data or []
    for row in rows:
        status = row.get("status") or "open"
        if status == "resolved":
            row["progress_percent"] = 100
            row["status_label"] = "Resolved"
        elif status == "in_review":
            row["progress_percent"] = 66
            row["status_label"] = "In review"
        elif status == "escalated":
            row["progress_percent"] = 80
            row["status_label"] = "Escalated"
        else:
            row["progress_percent"] = 33
            row["status_label"] = "Open"
    return rows


def get_activity_feed(user_id: str, limit: int = 10) -> list[dict]:
    """Returns recent status-change events for the user's reports + upvoted escalations."""
    activity = []

    try:
        reports_res = (
            supabase.table("reports")
            .select("id,status,created_at,resolved_at,hazard_type,department")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Activity fetch failed: {exc}")

    for r in reports_res.data or []:
        status = (r.get("status") or "open").lower()
        if status not in {"resolved", "in_review", "escalated"}:
            continue
        ts = r.get("resolved_at") or r.get("created_at")
        rid = _short_id(r.get("id", ""))
        if status == "resolved":
            msg = f"Your report #{rid} was resolved"
        elif status == "in_review":
            msg = f"Report #{rid} is now in review"
        else:
            msg = f"Report #{rid} was escalated"
        activity.append({
            "type": status,
            "report_id": r.get("id"),
            "message": msg,
            "timestamp": ts,
        })

    # Also include escalations for reports the user upvoted
    try:
        upvotes_res = supabase.table("upvotes").select("report_id").eq("user_id", user_id).execute()
        report_ids = [u.get("report_id") for u in (upvotes_res.data or []) if u.get("report_id")]
        if report_ids:
            escalated_res = (
                supabase.table("reports")
                .select("id,upvotes,created_at,status")
                .in_("id", report_ids)
                .gte("upvotes", 5)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            for r in escalated_res.data or []:
                rid = _short_id(r.get("id", ""))
                activity.append({
                    "type": "upvote_escalation",
                    "report_id": r.get("id"),
                    "message": f"Report #{rid} you upvoted hit {r.get('upvotes', 0)} upvotes",
                    "timestamp": r.get("created_at"),
                })
    except Exception as e:
        logger.warning(f"Upvote activity fetch failed: {e}")

    def _sort_key(item: dict):
        ts = item.get("timestamp")
        if not ts:
            return datetime.min
        try:
            return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except Exception:
            return datetime.min

    activity.sort(key=_sort_key, reverse=True)
    return activity[:limit]


def get_dashboard(user_id: str) -> dict:
    """Full user dashboard bundle: profile, stats, reports, activity, badges."""
    profile = get_profile(user_id)
    my_reports = get_user_reports(user_id)
    upvotes_given = get_upvotes_given_count(user_id)
    activity = get_activity_feed(user_id, limit=10)
    badges = get_badges_state(user_id)

    stats = {
        "reports_filed": int(profile.get("reports_submitted") or 0),
        "issues_resolved": int(profile.get("reports_resolved") or 0),
        "upvotes_given": upvotes_given,
    }

    return {
        "profile": profile,
        "stats": stats,
        "my_reports": my_reports,
        "activity": activity,
        "badges": badges,
    }
