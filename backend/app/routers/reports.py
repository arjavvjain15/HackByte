from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Any

from app.core.auth import get_current_user, get_current_user_id
from app.models.schemas import ReportCreateRequest, HazardType, SeverityLevel, ReportStatus
from app.services.reports import (
    create_report,
    list_reports,
    list_nearby_reports,
    list_user_reports,
    upvote_report,
    get_upvote_status,
    get_complaint_letter,
    build_share_payload,
)

router = APIRouter(prefix="/api", tags=["reports"])


@router.post("/reports")
def create_report_endpoint(
    payload: ReportCreateRequest,
    user: Any = Depends(get_current_user),
):
    user_id = get_current_user_id(user)
    report_payload = {
        "user_id": user_id,
        "photo_url": payload.photo_url,
        "lat": payload.lat,
        "lng": payload.lng,
        "hazard_type": payload.hazard_type,
        "severity": payload.severity,
        "department": payload.department,
        "summary": payload.summary,
        "complaint": payload.complaint_letter,
    }
    report = create_report(user_id, report_payload)
    return {"report": report}


@router.get("/reports")
def list_reports_endpoint(
    severity: SeverityLevel | None = Query(default=None),
    status: ReportStatus | None = Query(default=None),
    hazard_type: HazardType | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=1000),
):
    reports = list_reports(severity=severity, status=status, hazard_type=hazard_type, limit=limit)
    return {"reports": reports}


@router.get("/reports/nearby")
def nearby_reports_endpoint(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius: int = Query(default=2000, ge=100, le=50000),
    _user: Any = Depends(get_current_user),
):
    reports = list_nearby_reports(lat, lng, radius)
    return {"reports": reports}


@router.get("/reports/mine")
def my_reports_endpoint(
    user: Any = Depends(get_current_user),
):
    user_id = get_current_user_id(user)
    reports = list_user_reports(user_id)
    return {"reports": reports}


@router.post("/reports/{report_id}/upvote")
def upvote_report_endpoint(
    report_id: str,
    user: Any = Depends(get_current_user),
):
    user_id = get_current_user_id(user)
    if not report_id:
        raise HTTPException(status_code=400, detail="Missing report id")
    result = upvote_report(report_id, user_id)
    return result


@router.get("/reports/{report_id}/upvote-status")
def upvote_status_endpoint(
    report_id: str,
    user: Any = Depends(get_current_user),
):
    user_id = get_current_user_id(user)
    if not report_id:
        raise HTTPException(status_code=400, detail="Missing report id")
    return get_upvote_status(report_id, user_id)


@router.get("/reports/{report_id}/complaint-letter")
def complaint_letter_endpoint(
    report_id: str,
    user: Any = Depends(get_current_user),
):
    user_id = get_current_user_id(user)
    report = get_complaint_letter(report_id, user_id)
    return {
        "report_id": report.get("id"),
        "complaint_letter": report.get("complaint"),
        "department": report.get("department"),
        "hazard_type": report.get("hazard_type"),
    }


@router.get("/reports/{report_id}/share-payload")
def share_payload_endpoint(
    report_id: str,
    user: Any = Depends(get_current_user),
):
    user_id = get_current_user_id(user)
    report = get_complaint_letter(report_id, user_id)
    return build_share_payload(report)
