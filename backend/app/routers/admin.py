from fastapi import APIRouter, Depends, Query
from typing import Any

from app.core.auth import get_current_user, require_admin
from app.models.schemas import (
    AdminBulkUpdateRequest,
    HazardType,
    SeverityLevel,
    ReportStatus,
    AdminSortType,
)
from app.services.reports import list_admin_reports, bulk_update_reports, admin_stats

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/reports")
def admin_list_reports(
    user: Any = Depends(get_current_user),
    severity: SeverityLevel | None = Query(default=None),
    status: ReportStatus | None = Query(default=None),
    hazard_type: HazardType | None = Query(default=None),
    area_name: str | None = Query(default=None, min_length=2, max_length=120),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    sort: AdminSortType = Query(default="newest"),
    limit: int = Query(default=500, ge=1, le=1000),
):
    require_admin(user)
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
    return {"reports": reports}


@router.patch("/reports")
def admin_bulk_update(
    payload: AdminBulkUpdateRequest,
    user: Any = Depends(get_current_user),
):
    require_admin(user)
    result = bulk_update_reports(payload.ids, payload.status)
    return result


@router.get("/stats")
def admin_stats_endpoint(
    user: Any = Depends(get_current_user),
):
    require_admin(user)
    return admin_stats()
