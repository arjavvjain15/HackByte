from fastapi import APIRouter, Depends
from typing import Any

from app.core.auth import get_current_user, require_admin
from app.models.schemas import AdminBulkUpdateRequest
from app.services.reports import list_admin_reports, bulk_update_reports, admin_stats

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/reports")
def admin_list_reports(
    user: Any = Depends(get_current_user),
):
    require_admin(user)
    reports = list_admin_reports()
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
