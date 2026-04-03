from fastapi import APIRouter, Depends, Query
from typing import Any

from app.core.auth import get_current_user, get_current_user_id
from app.models.schemas import ReportCreateRequest
from app.services.reports import create_report, list_reports, list_nearby_reports, list_user_reports

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
    severity: str | None = Query(default=None),
    status: str | None = Query(default=None),
    hazard_type: str | None = Query(default=None),
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
