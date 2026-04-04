from fastapi import APIRouter, UploadFile, File, Depends
from typing import Any

from app.core.auth import get_current_user
from app.models.schemas import PresignRequest
from app.services.storage import upload_photo_to_storage, create_presigned_upload

router = APIRouter(prefix="/api", tags=["uploads"])


@router.post("/upload")
async def upload_photo(
    file: UploadFile = File(...),
    _user: Any = Depends(get_current_user),
):
    data = await file.read()
    filename = file.filename or "photo"
    content_type = file.content_type or "application/octet-stream"
    return upload_photo_to_storage(data, filename, content_type)


@router.post("/uploads/presign")
def presign_upload(
    payload: PresignRequest,
    _user: Any = Depends(get_current_user),
):
    filename = payload.filename or "photo.jpg"
    return create_presigned_upload(filename, payload.content_type)
