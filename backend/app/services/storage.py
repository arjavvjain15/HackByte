"""
EcoSnap — Storage Service
Uploads photos to Supabase Storage via the Storage REST API (httpx).
No supabase-py SDK required — fully Python 3.14 compatible.
"""
import os
import logging
from uuid import uuid4
from fastapi import HTTPException
import httpx

from app.config import SUPABASE_URL, SUPABASE_SERVICE_KEY

logger = logging.getLogger(__name__)

STORAGE_BUCKET = os.environ.get("SUPABASE_STORAGE_BUCKET", "hazard-photos")
STORAGE_BASE = f"{SUPABASE_URL}/storage/v1" if SUPABASE_URL else ""

HEADERS = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
}


def _public_url(path: str) -> str:
    return f"{STORAGE_BASE}/object/public/{STORAGE_BUCKET}/{path}"


def upload_photo_to_storage(data: bytes, filename: str, content_type: str) -> dict:
    """Upload a photo directly to Supabase Storage. Returns public URL."""
    if not content_type or not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are allowed")
    if not data:
        raise HTTPException(status_code=400, detail="Empty file body")

    ext = os.path.splitext(filename)[1].lower() or ".jpg"
    path = f"{uuid4().hex}{ext}"

    upload_url = f"{STORAGE_BASE}/object/{STORAGE_BUCKET}/{path}"
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                upload_url,
                content=data,
                headers={
                    **HEADERS,
                    "Content-Type": content_type,
                    "x-upsert": "false",
                },
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Storage upload request failed: {exc}")

    if response.status_code not in (200, 201):
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {response.status_code} {response.text}")

    public_url = _public_url(path)
    return {"bucket": STORAGE_BUCKET, "path": path, "public_url": public_url}


def create_presigned_upload(filename: str, content_type: str | None) -> dict:
    """Creates a signed upload URL for direct browser-to-storage uploads."""
    ext = os.path.splitext(filename)[1].lower() or ".jpg"
    path = f"{uuid4().hex}{ext}"

    presign_url = f"{STORAGE_BASE}/object/upload/sign/{STORAGE_BUCKET}/{path}"
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(presign_url, headers=HEADERS, json={})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Presign request failed: {exc}")

    if response.status_code not in (200, 201):
        raise HTTPException(status_code=500, detail=f"Presign failed: {response.status_code} {response.text}")

    data = response.json()
    signed_url = data.get("signedURL") or data.get("signedUrl") or data.get("signed_url")
    if not signed_url:
        raise HTTPException(status_code=500, detail="Presign failed: no signed URL returned")

    return {
        "bucket": STORAGE_BUCKET,
        "path": path,
        "signed_url": signed_url,
        "public_url": _public_url(path),
        "content_type": content_type,
    }
