from fastapi import APIRouter, Depends, Query
from typing import Any

from app.core.auth import get_current_user, require_admin
from app.models.schemas import (
    AdminBulkUpdateRequest,
    AdminAssignDepartmentRequest,
    HazardType,
    SeverityLevel,
    ReportStatus,
    AdminSortType,
)
from app.services.reports import (
    list_admin_reports,
    bulk_update_reports,
    admin_stats,
    list_escalations,
    assign_department,
    get_admin_breakdown,
    export_reports_csv,
    get_admin_dashboard_bundle,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/reports")
def admin_list_reports(
    user: Any = Depends(get_current_user),
    severity: SeverityLevel | None = Query(default=None),
    status: ReportStatus | None = Query(default=None),
    hazard_type: HazardType | None = Query(default=None),
    area: str | None = Query(default=None, min_length=2, max_length=120),
    area_name: str | None = Query(default=None, min_length=2, max_length=120),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    sort: AdminSortType = Query(default="newest"),
    limit: int = Query(default=500, ge=1, le=1000),
):
    require_admin(user)
    area_filter = area_name or area
    reports = list_admin_reports(
        severity=severity,
        status=status,
        hazard_type=hazard_type,
        area_name=area_filter,
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


@router.get("/escalations")
def admin_escalations_endpoint(
    user: Any = Depends(get_current_user),
    severity: SeverityLevel | None = Query(default=None),
    hazard_type: HazardType | None = Query(default=None),
    area: str | None = Query(default=None, min_length=2, max_length=120),
    area_name: str | None = Query(default=None, min_length=2, max_length=120),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    sort: AdminSortType = Query(default="most_upvoted"),
    limit: int = Query(default=500, ge=1, le=1000),
    min_upvotes: int = Query(default=5, ge=5, le=1000),
):
    require_admin(user)
    area_filter = area_name or area
    escalations = list_escalations(
        severity=severity,
        hazard_type=hazard_type,
        area_name=area_filter,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
        limit=limit,
        min_upvotes=min_upvotes,
    )
    return {"reports": escalations, "count": len(escalations)}


@router.patch("/reports/assign-department")
def admin_assign_department(
    payload: AdminAssignDepartmentRequest,
    user: Any = Depends(get_current_user),
):
    require_admin(user)
    return assign_department(payload.ids, payload.department)


@router.get("/breakdown")
def admin_breakdown(
    user: Any = Depends(get_current_user),
    severity: SeverityLevel | None = Query(default=None),
    status: ReportStatus | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
):
    require_admin(user)
    return get_admin_breakdown(
        date_from=date_from,
        date_to=date_to,
        severity=severity,
        status=status,
    )


@router.get("/reports/export")
def admin_export_reports(
    user: Any = Depends(get_current_user),
    severity: SeverityLevel | None = Query(default=None),
    status: ReportStatus | None = Query(default=None),
    hazard_type: HazardType | None = Query(default=None),
    area: str | None = Query(default=None, min_length=2, max_length=120),
    area_name: str | None = Query(default=None, min_length=2, max_length=120),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    sort: AdminSortType = Query(default="newest"),
    limit: int = Query(default=2000, ge=1, le=5000),
):
    require_admin(user)
    area_filter = area_name or area
    csv_text = export_reports_csv(
        severity=severity,
        status=status,
        hazard_type=hazard_type,
        area_name=area_filter,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
        limit=limit,
    )
    return {"csv": csv_text}


@router.get("/dashboard")
def admin_dashboard_bundle(
    user: Any = Depends(get_current_user),
    severity: SeverityLevel | None = Query(default=None),
    status: ReportStatus | None = Query(default=None),
    hazard_type: HazardType | None = Query(default=None),
    area: str | None = Query(default=None, min_length=2, max_length=120),
    area_name: str | None = Query(default=None, min_length=2, max_length=120),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    sort: AdminSortType = Query(default="newest"),
    limit: int = Query(default=500, ge=1, le=1000),
    include_escalations: bool = Query(default=False),
):
    require_admin(user)
    area_filter = area_name or area
    return get_admin_dashboard_bundle(
        severity=severity,
        status=status,
        hazard_type=hazard_type,
        area_name=area_filter,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
        limit=limit,
        include_escalations=include_escalations,
    )
