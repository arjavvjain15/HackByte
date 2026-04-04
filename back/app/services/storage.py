import os
from uuid import uuid4
from fastapi import HTTPException

from app.core.config import get_optional_env
from app.core.supabase import get_supabase_client


def upload_photo_to_storage(
    data: bytes,
    filename: str,
    content_type: str,
) -> dict:
    if not content_type or not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are allowed")

    bucket = get_optional_env("SUPABASE_STORAGE_BUCKET", "hazard-photos")
    ext = os.path.splitext(filename)[1].lower()
    if not ext:
        ext = ".jpg"

    path = f"{uuid4().hex}{ext}"
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    client = get_supabase_client()
    storage = client.storage.from_(bucket)
    upload_res = storage.upload(
        path,
        data,
        file_options={"content-type": content_type, "upsert": False},
    )

    if hasattr(upload_res, "error") and upload_res.error:
        raise HTTPException(status_code=500, detail=str(upload_res.error))

    public_url = storage.get_public_url(path)
    return {"bucket": bucket, "path": path, "public_url": public_url}


def create_presigned_upload(filename: str, content_type: str | None) -> dict:
    bucket = get_optional_env("SUPABASE_STORAGE_BUCKET", "hazard-photos")
    ext = os.path.splitext(filename)[1].lower()
    if not ext:
        ext = ".jpg"

    path = f"{uuid4().hex}{ext}"
    client = get_supabase_client()
    storage = client.storage.from_(bucket)
    result = storage.create_signed_upload_url(path)

    signed_url = None
    token = None
    if isinstance(result, dict):
        signed_url = result.get("signedUrl") or result.get("signed_url")
        token = result.get("token")

    if not signed_url:
        raise HTTPException(status_code=500, detail="Presign failed: no signed URL")

    public_url = storage.get_public_url(path)
    return {
        "bucket": bucket,
        "path": path,
        "signed_url": signed_url,
        "token": token,
        "public_url": public_url,
        "content_type": content_type,
    }
