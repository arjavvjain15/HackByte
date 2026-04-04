from datetime import datetime, timezone
from collections import Counter
from fastapi import HTTPException
import math
from urllib.parse import quote

from app.core.supabase import get_supabase_client
from app.services.badges import ensure_badges


ALLOWED_STATUSES = {"open", "in_review", "resolved", "escalated"}
SEVERITY_RANK = {"high": 3, "medium": 2, "low": 1}


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

    try:
        ensure_badges(user_id)
    except Exception:
        pass
    return report_data


def list_admin_reports(
    severity: str | None = None,
    status: str | None = None,
    hazard_type: str | None = None,
    area_name: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sort: str = "newest",
    limit: int = 500,
) -> list[dict]:
    client = get_supabase_client()
    try:
        query = client.table("reports").select("*")
        if severity:
            query = query.eq("severity", severity)
        if status:
            query = query.eq("status", status)
        if hazard_type:
            query = query.eq("hazard_type", hazard_type)
        if date_from:
            query = query.gte("created_at", date_from)
        if date_to:
            query = query.lte("created_at", date_to)

        if sort == "most_upvoted":
            query = query.order("upvotes", desc=True)
        elif sort == "newest":
            query = query.order("created_at", desc=True)
        elif sort == "oldest":
            query = query.order("created_at", desc=False)
        else:
            query = query.order("created_at", desc=True)

        result = query.limit(limit).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Fetch failed: {exc}") from exc
    data = result.data or []
    if area_name:
        normalized = area_name.strip().lower()
        area_keys = ["area", "area_name", "location_name", "location", "address"]
        data = [
            row
            for row in data
            if any(normalized in str(row.get(key, "")).lower() for key in area_keys)
        ]
    if sort == "highest_severity":
        data.sort(key=lambda r: SEVERITY_RANK.get(r.get("severity") or "", 0), reverse=True)
    return data


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
                try:
                    ensure_badges(user_id)
                except Exception:
                    pass
            except Exception:
                continue

    return {
        "updated_reports": updated_count,
        "updated_profiles": updated_profiles,
        "status": status,
    }


def assign_department(ids: list[str], department: str) -> dict:
    if not ids:
        raise HTTPException(status_code=400, detail="No report ids provided")
    client = get_supabase_client()
    try:
        reports_res = client.table("reports").select("id").in_("id", ids).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Fetch failed: {exc}") from exc

    reports = reports_res.data or []
    if not reports:
        raise HTTPException(status_code=404, detail="No reports found for ids")

    try:
        client.table("reports").update({"department": department}).in_("id", ids).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Department update failed: {exc}") from exc

    return {"updated_reports": len(reports), "department": department}


def list_reports(
    severity: str | None = None,
    status: str | None = None,
    hazard_type: str | None = None,
    area_name: str | None = None,
    user_id: str | None = None,
    limit: int = 500,
) -> list[dict]:
    client = get_supabase_client()
    query = client.table("reports").select(
        "id,user_id,lat,lng,hazard_type,severity,department,summary,upvotes,status,created_at,area,area_name,location,location_name,address"
    )
    if severity:
        query = query.eq("severity", severity)
    if status:
        query = query.eq("status", status)
    if hazard_type:
        query = query.eq("hazard_type", hazard_type)
    if user_id:
        query = query.eq("user_id", user_id)

    try:
        result = query.order("created_at", desc=True).limit(limit).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Fetch failed: {exc}") from exc
    data = result.data or []
    if area_name:
        normalized = area_name.strip().lower()
        area_keys = ["area", "area_name", "location_name", "location", "address"]
        data = [
            row
            for row in data
            if any(normalized in str(row.get(key, "")).lower() for key in area_keys)
        ]
    return data


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


def _format_distance_km(distance_m: float) -> str:
    try:
        km = float(distance_m) / 1000.0
    except Exception:
        km = 0.0
    return f"{km:.1f} km"


def list_nearby_reports(lat: float, lng: float, radius_m: int, user_id: str | None = None) -> list[dict]:
    client = get_supabase_client()
    # Prefer database-side distance filtering if the function exists.
    try:
        rpc_res = client.rpc(
            "nearby_reports",
            {"lat": lat, "lng": lng, "radius_m": radius_m},
        ).execute()
        if getattr(rpc_res, "data", None) is not None:
            rows = rpc_res.data or []
            if user_id:
                try:
                    upvotes_res = (
                        client.table("upvotes")
                        .select("report_id")
                        .eq("user_id", user_id)
                        .execute()
                    )
                    voted_ids = {r.get("report_id") for r in (upvotes_res.data or [])}
                except Exception:
                    voted_ids = set()
                for row in rows:
                    row["voted"] = row.get("id") in voted_ids
            for row in rows:
                if "distance_m" in row and row.get("distance_m") is not None:
                    row["distance_km"] = _format_distance_km(row["distance_m"])
            return rows
    except Exception:
        # Fallback to Python filtering if RPC isn't available.
        pass
    try:
        result = client.table("reports").select(
            "id,lat,lng,hazard_type,severity,upvotes,status,created_at,area,area_name,location,location_name,address"
        ).execute()
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
            report["distance_km"] = _format_distance_km(distance)
            nearby.append(report)

    if user_id:
        try:
            upvotes_res = (
                client.table("upvotes")
                .select("report_id")
                .eq("user_id", user_id)
                .execute()
            )
            voted_ids = {r.get("report_id") for r in (upvotes_res.data or [])}
        except Exception:
            voted_ids = set()
        for report in nearby:
            report["voted"] = report.get("id") in voted_ids

    nearby.sort(key=lambda r: r.get("distance_m", 0))
    return nearby


def upvote_report(report_id: str, user_id: str) -> dict:
    client = get_supabase_client()
    try:
        report_res = (
            client.table("reports")
            .select("id,user_id,upvotes,status")
            .eq("id", report_id)
            .single()
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Report not found: {exc}") from exc

    if not isinstance(report_res.data, dict):
        raise HTTPException(status_code=404, detail="Report not found")

    try:
        insert_res = client.table("upvotes").insert(
            {"report_id": report_id, "user_id": user_id}
        ).execute()
    except Exception as exc:
        message = str(exc).lower()
        if "duplicate" in message or "23505" in message:
            raise HTTPException(status_code=409, detail="User already upvoted") from exc
        raise HTTPException(status_code=500, detail=f"Upvote failed: {exc}") from exc

    if not getattr(insert_res, "data", None):
        raise HTTPException(status_code=500, detail="Upvote failed: no data returned")

    current_upvotes = int(report_res.data.get("upvotes") or 0)
    current_status = report_res.data.get("status")
    report_owner_id = report_res.data.get("user_id")

    new_upvotes = current_upvotes + 1
    update_payload = {"upvotes": new_upvotes}
    if new_upvotes >= 5 and current_status != "escalated":
        update_payload["status"] = "escalated"

    try:
        client.table("reports").update(update_payload).eq("id", report_id).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Report update failed: {exc}") from exc

    if report_owner_id:
        try:
            ensure_badges(report_owner_id)
        except Exception:
            pass

    return {
        "report_id": report_id,
        "upvotes": new_upvotes,
        "status": update_payload.get("status", current_status or "open"),
    }


def get_upvote_status(report_id: str, user_id: str) -> dict:
    client = get_supabase_client()
    try:
        upvote_res = (
            client.table("upvotes")
            .select("id")
            .eq("report_id", report_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upvote status failed: {exc}") from exc

    try:
        report_res = client.table("reports").select("upvotes,status").eq("id", report_id).single().execute()
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Report not found: {exc}") from exc

    voted = bool(upvote_res.data)
    upvotes = 0
    status = "open"
    if isinstance(report_res.data, dict):
        upvotes = int(report_res.data.get("upvotes") or 0)
        status = report_res.data.get("status") or "open"

    return {"report_id": report_id, "voted": voted, "upvotes": upvotes, "status": status}


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


def _is_admin_user(user_id: str) -> bool:
    client = get_supabase_client()
    try:
        profile = client.table("profiles").select("is_admin").eq("id", user_id).single().execute()
    except Exception:
        return False
    if isinstance(profile.data, dict):
        return bool(profile.data.get("is_admin"))
    return False


def get_complaint_letter(report_id: str, requester_user_id: str) -> dict:
    client = get_supabase_client()
    try:
        report_res = (
            client.table("reports")
            .select("id,user_id,hazard_type,department,complaint,created_at,lat,lng,photo_url")
            .eq("id", report_id)
            .single()
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Report not found: {exc}") from exc

    report = report_res.data if isinstance(report_res.data, dict) else None
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    is_owner = report.get("user_id") == requester_user_id
    if not is_owner and not _is_admin_user(requester_user_id):
        raise HTTPException(status_code=403, detail="Access denied for complaint letter")

    complaint = report.get("complaint")
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint letter not available")
    return report


def build_share_payload(report: dict) -> dict:
    report_id = report.get("id")
    department = report.get("department") or "Concerned Department"
    hazard_type = report.get("hazard_type") or "environmental_hazard"
    lat = report.get("lat")
    lng = report.get("lng")
    photo_url = report.get("photo_url") or ""
    complaint = report.get("complaint") or ""
    created_at = report.get("created_at") or datetime.now(timezone.utc).isoformat()

    subject = f"EcoSnap Report {report_id} - {hazard_type}"
    text = (
        f"To: {department}\n"
        f"Date: {created_at}\n"
        f"Subject: {hazard_type}\n\n"
        f"{complaint}\n\n"
        f"Photo evidence: {photo_url}\n"
        f"GPS coordinates: {lat}, {lng}\n"
        f"Report ID: {report_id}"
    )
    whatsapp_text = quote(text, safe="")
    mailto_subject = quote(subject, safe="")
    mailto_body = quote(text, safe="")
    return {
        "title": "EcoSnap Report",
        "text": text,
        "copy_text": text,
        "mailto_url": f"mailto:?subject={mailto_subject}&body={mailto_body}",
        "whatsapp_url": f"https://wa.me/?text={whatsapp_text}",
    }


def share_payload_for_channel(report: dict, channel: str) -> dict:
    payload = build_share_payload(report)
    if channel == "email":
        return {
            "channel": channel,
            "title": payload["title"],
            "text": payload["text"],
            "target_url": payload["mailto_url"],
        }
    if channel == "whatsapp":
        return {
            "channel": channel,
            "title": payload["title"],
            "text": payload["text"],
            "target_url": payload["whatsapp_url"],
        }
    if channel == "copy":
        return {
            "channel": channel,
            "title": payload["title"],
            "text": payload["copy_text"],
            "target_url": None,
        }
    return {
        "channel": "native",
        "title": payload["title"],
        "text": payload["text"],
        "target_url": None,
    }


def list_escalations(
    severity: str | None = None,
    hazard_type: str | None = None,
    area_name: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sort: str = "most_upvoted",
    limit: int = 500,
    min_upvotes: int = 5,
) -> list[dict]:
    client = get_supabase_client()
    try:
        query = client.table("reports").select("*")
        if severity:
            query = query.eq("severity", severity)
        if hazard_type:
            query = query.eq("hazard_type", hazard_type)
        if date_from:
            query = query.gte("created_at", date_from)
        if date_to:
            query = query.lte("created_at", date_to)
        query = query.gte("upvotes", min_upvotes)

        if sort == "newest":
            query = query.order("created_at", desc=True)
        elif sort == "oldest":
            query = query.order("created_at", desc=False)
        elif sort == "highest_severity":
            query = query.order("created_at", desc=True)
        else:
            query = query.order("upvotes", desc=True)

        result = query.limit(limit).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Escalations fetch failed: {exc}") from exc

    data = result.data or []
    data = [row for row in data if row.get("status") == "escalated" or int(row.get("upvotes") or 0) >= min_upvotes]
    if area_name:
        normalized = area_name.strip().lower()
        area_keys = ["area", "area_name", "location_name", "location", "address"]
        data = [
            row
            for row in data
            if any(normalized in str(row.get(key, "")).lower() for key in area_keys)
        ]
    if sort == "highest_severity":
        data.sort(key=lambda r: SEVERITY_RANK.get(r.get("severity") or "", 0), reverse=True)
    return data


def get_admin_breakdown(
    date_from: str | None = None,
    date_to: str | None = None,
    severity: str | None = None,
    status: str | None = None,
) -> dict:
    client = get_supabase_client()
    try:
        query = client.table("reports").select("hazard_type,area,area_name,location,location_name,address")
        if date_from:
            query = query.gte("created_at", date_from)
        if date_to:
            query = query.lte("created_at", date_to)
        if severity:
            query = query.eq("severity", severity)
        if status:
            query = query.eq("status", status)
        result = query.execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Breakdown fetch failed: {exc}") from exc

    rows = result.data or []
    by_type = Counter([r.get("hazard_type") or "other" for r in rows])
    by_area = Counter(
        [
            (r.get("area") or r.get("area_name") or r.get("location_name") or r.get("location") or r.get("address") or "Unknown")
            for r in rows
        ]
    )

    return {
        "by_type": [{"label": k, "count": v} for k, v in by_type.most_common()],
        "by_area": [{"label": k, "count": v} for k, v in by_area.most_common()],
    }


def export_reports_csv(
    severity: str | None = None,
    status: str | None = None,
    hazard_type: str | None = None,
    area_name: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sort: str = "newest",
    limit: int = 2000,
) -> str:
    rows = list_admin_reports(
        severity=severity,
        status=status,
        hazard_type=hazard_type,
        area_name=area_name,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
        limit=limit,
    )
    headers = [
        "id",
        "created_at",
        "hazard_type",
        "severity",
        "status",
        "upvotes",
        "department",
        "lat",
        "lng",
    ]
    lines = [",".join(headers)]
    for r in rows:
        line = [
            str(r.get("id", "")),
            str(r.get("created_at", "")),
            str(r.get("hazard_type", "")),
            str(r.get("severity", "")),
            str(r.get("status", "")),
            str(r.get("upvotes", "")),
            str(r.get("department", "")),
            str(r.get("lat", "")),
            str(r.get("lng", "")),
        ]
        line = [v.replace(",", " ") if isinstance(v, str) else str(v) for v in line]
        lines.append(",".join(line))
    return "\n".join(lines)


def get_admin_dashboard_bundle(
    severity: str | None = None,
    status: str | None = None,
    hazard_type: str | None = None,
    area_name: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sort: str = "newest",
    limit: int = 500,
    include_escalations: bool = False,
) -> dict:
    stats = admin_stats()
    reports = list_admin_reports(
        severity=severity,
        status=status,
        hazard_type=hazard_type,
        area_name=area_name,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
        limit=limit,
    )
    breakdown = get_admin_breakdown(
        date_from=date_from,
        date_to=date_to,
        severity=severity,
        status=status,
    )
    bundle = {
        "stats": stats,
        "reports": reports,
        "breakdown": breakdown,
    }
    if include_escalations:
        escalations = list_escalations(
            severity=severity,
            hazard_type=hazard_type,
            area_name=area_name,
            date_from=date_from,
            date_to=date_to,
            sort="most_upvoted",
            limit=limit,
            min_upvotes=5,
        )
        bundle["escalations"] = escalations
        bundle["escalations_count"] = len(escalations)
    return bundle
