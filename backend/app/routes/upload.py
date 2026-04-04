"""
EcoSnap — Upload Routes
POST /api/upload          — Direct multipart upload
POST /api/uploads/presign — Generate a presigned URL for browser-side upload
"""
import logging
from fastapi import APIRouter, UploadFile, File, Depends
from typing import Any

from app.core.auth import get_current_user
from app.services.storage import upload_photo_to_storage, create_presigned_upload

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Uploads"])


class PresignRequest:
    def __init__(self, filename: str | None = None, content_type: str | None = None):
        self.filename = filename
        self.content_type = content_type


@router.post("/upload")
async def upload_photo(
    file: UploadFile = File(...),
    _user: Any = Depends(get_current_user),
):
    """Upload a photo file directly to Supabase Storage. Returns the public URL."""
    data = await file.read()
    filename = file.filename or "photo"
    content_type = file.content_type or "image/jpeg"
    return upload_photo_to_storage(data, filename, content_type)


from pydantic import BaseModel

class PresignPayload(BaseModel):
    filename: str | None = None
    content_type: str | None = None


@router.post("/uploads/presign")
def presign_upload(
    payload: PresignPayload,
    _user: Any = Depends(get_current_user),
):
    """
    Generate a presigned upload URL for direct browser → Supabase Storage uploads.
    The frontend can PUT the file directly to the signed_url.
    """
    filename = payload.filename or "photo.jpg"
    return create_presigned_upload(filename, payload.content_type)
