from datetime import datetime
from fastapi import HTTPException

from app.core.supabase import get_supabase_client
from app.services.reports import list_user_reports


def _short_id(report_id: str) -> str:
    if not report_id:
        return ""
    return report_id.split("-")[-1][:4]


def get_profile(user_id: str) -> dict:
    client = get_supabase_client()
    try:
        result = (
            client.table("profiles")
            .select("id,display_name,avatar_url,is_admin,reports_submitted,reports_resolved,created_at")
            .eq("id", user_id)
            .single()
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Profile not found: {exc}") from exc

    if not isinstance(result.data, dict):
        raise HTTPException(status_code=404, detail="Profile not found")
    return result.data


def get_upvotes_given_count(user_id: str) -> int:
    client = get_supabase_client()
    try:
        result = client.table("upvotes").select("id").eq("user_id", user_id).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upvotes fetch failed: {exc}") from exc
    return len(result.data or [])


def get_activity_feed(user_id: str, limit: int = 10) -> list[dict]:
    client = get_supabase_client()
    activity = []

    try:
        reports_res = (
            client.table("reports")
            .select("id,status,created_at,resolved_at,hazard_type,department,area,area_name,location,location_name,address")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Activity fetch failed: {exc}") from exc

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

    try:
        upvotes_res = client.table("upvotes").select("report_id").eq("user_id", user_id).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upvotes fetch failed: {exc}") from exc

    report_ids = [u.get("report_id") for u in upvotes_res.data or [] if u.get("report_id")]
    if report_ids:
        try:
            escalated_res = (
                client.table("reports")
                .select("id,upvotes,created_at,status")
                .in_("id", report_ids)
                .gte("upvotes", 5)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Escalations fetch failed: {exc}") from exc

        for r in escalated_res.data or []:
            rid = _short_id(r.get("id", ""))
            msg = f"Report #{rid} you upvoted hit {r.get('upvotes', 0)} upvotes"
            activity.append({
                "type": "upvote_escalation",
                "report_id": r.get("id"),
                "message": msg,
                "timestamp": r.get("created_at"),
            })

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
    profile = get_profile(user_id)
    my_reports = list_user_reports(user_id)
    upvotes_given = get_upvotes_given_count(user_id)
    activity = get_activity_feed(user_id, limit=10)

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
    }
