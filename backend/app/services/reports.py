from datetime import datetime, timezone
from collections import Counter
from fastapi import HTTPException
import math

from app.core.supabase import get_supabase_client


ALLOWED_STATUSES = {"open", "in_review", "resolved", "escalated"}


def create_report(user_id: str, payload: dict) -> dict:
    client = get_supabase_client()
    try:
        insert_res = client.table("reports").insert(payload).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Report insert failed: {exc}") from exc

    report_data = insert_res.data[0] if getattr(insert_res, "data", None) else None
    if not report_data:
        raise HTTPException(status_code=500, detail="Report insert failed: no data returned")

    try:
        profile_res = (
            client.table("profiles")
            .select("reports_submitted")
            .eq("id", user_id)
            .single()
            .execute()
        )
        current_count = 0
        if isinstance(profile_res.data, dict):
            current_count = int(profile_res.data.get("reports_submitted") or 0)
        client.table("profiles").update(
            {"reports_submitted": current_count + 1}
        ).eq("id", user_id).execute()
    except Exception:
        pass

    return report_data


def list_admin_reports() -> list[dict]:
    client = get_supabase_client()
    try:
        result = client.table("reports").select("*").order("created_at", desc=True).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Fetch failed: {exc}") from exc
    return result.data or []


def bulk_update_reports(ids: list[str], status: str) -> dict:
    if status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")
    if not ids:
        raise HTTPException(status_code=400, detail="No report ids provided")

    client = get_supabase_client()
    try:
        reports_res = client.table("reports").select("id,user_id").in_("id", ids).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Fetch failed: {exc}") from exc

    reports = reports_res.data or []
    if not reports:
        raise HTTPException(status_code=404, detail="No reports found for ids")

    update_payload = {"status": status}
    if status == "resolved":
        update_payload["resolved_at"] = datetime.now(timezone.utc).isoformat()
    else:
        update_payload["resolved_at"] = None

    try:
        client.table("reports").update(update_payload).in_("id", ids).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Update failed: {exc}") from exc

    updated_count = len(reports)
    updated_profiles = 0

    if status == "resolved":
        user_counts = Counter([r.get("user_id") for r in reports if r.get("user_id")])
        for user_id, count in user_counts.items():
            try:
                profile_res = (
                    client.table("profiles")
                    .select("reports_resolved")
                    .eq("id", user_id)
                    .single()
                    .execute()
                )
                current_count = 0
                if isinstance(profile_res.data, dict):
                    current_count = int(profile_res.data.get("reports_resolved") or 0)
                client.table("profiles").update(
                    {"reports_resolved": current_count + count}
                ).eq("id", user_id).execute()
                updated_profiles += 1
            except Exception:
                continue

    return {
        "updated_reports": updated_count,
        "updated_profiles": updated_profiles,
        "status": status,
    }


def list_reports(
    severity: str | None = None,
    status: str | None = None,
    hazard_type: str | None = None,
    limit: int = 500,
) -> list[dict]:
    client = get_supabase_client()
    query = client.table("reports").select(
        "id,lat,lng,hazard_type,severity,upvotes,status,created_at"
    )
    if severity:
        query = query.eq("severity", severity)
    if status:
        query = query.eq("status", status)
    if hazard_type:
        query = query.eq("hazard_type", hazard_type)

    try:
        result = query.order("created_at", desc=True).limit(limit).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Fetch failed: {exc}") from exc
    return result.data or []


def list_user_reports(user_id: str) -> list[dict]:
    client = get_supabase_client()
    try:
        result = (
            client.table("reports")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Fetch failed: {exc}") from exc
    return result.data or []


def list_nearby_reports(lat: float, lng: float, radius_m: int) -> list[dict]:
    client = get_supabase_client()
    try:
        result = (
            client.table("reports")
            .select("id,lat,lng,hazard_type,severity,upvotes,status,created_at")
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Fetch failed: {exc}") from exc

    reports = result.data or []
    if not reports:
        return []

    def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        r = 6371000.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lng2 - lng1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return r * c

    nearby = []
    for report in reports:
        try:
            rlat = float(report.get("lat"))
            rlng = float(report.get("lng"))
        except Exception:
            continue
        distance = haversine_m(lat, lng, rlat, rlng)
        if distance <= radius_m:
            report["distance_m"] = round(distance, 2)
            nearby.append(report)

    nearby.sort(key=lambda r: r.get("distance_m", 0))
    return nearby


def admin_stats() -> dict:
    client = get_supabase_client()
    try:
        reports_res = client.table("reports").select("status,created_at,resolved_at,upvotes").execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Stats fetch failed: {exc}") from exc

    reports = reports_res.data or []
    counts = Counter([r.get("status") or "open" for r in reports])
    escalated = sum(1 for r in reports if r.get("status") == "escalated" or (r.get("upvotes") or 0) >= 5)

    resolution_times = []
    for r in reports:
        if r.get("resolved_at") and r.get("created_at"):
            try:
                created = datetime.fromisoformat(str(r.get("created_at")).replace("Z", "+00:00"))
                resolved = datetime.fromisoformat(str(r.get("resolved_at")).replace("Z", "+00:00"))
                resolution_times.append((resolved - created).total_seconds())
            except Exception:
                continue

    avg_resolution_hours = (
        round(sum(resolution_times) / len(resolution_times) / 3600, 2) if resolution_times else 0.0
    )

    return {
        "open": counts.get("open", 0),
        "in_review": counts.get("in_review", 0),
        "resolved": counts.get("resolved", 0),
        "escalated": escalated,
        "avg_resolution_hours": avg_resolution_hours,
    }
