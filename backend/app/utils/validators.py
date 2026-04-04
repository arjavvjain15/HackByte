"""
EcoSnap — Pydantic Schemas & Output Validation
"""
from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel, HttpUrl, field_validator
import re


# ── Allowed enum values ────────────────────────────────────────────────────────
VALID_HAZARD_TYPES = {
    "illegal_dumping",
    "oil_spill",
    "e_waste",
    "water_pollution",
    "blocked_drain",
    "air_pollution",
    "other",
}

VALID_SEVERITIES = {"high", "medium", "low"}


# ── Request schemas ────────────────────────────────────────────────────────────

class ClassifyRequest(BaseModel):
    photo_url: str
    lat: float = 0.0
    lng: float = 0.0
    user_name: Optional[str] = "Anonymous"


class ReportCreate(BaseModel):
    user_id: Optional[str] = None
    photo_url: str
    lat: float = 0.0
    lng: float = 0.0
    hazard_type: str
    severity: str
    department: str
    summary: Optional[str] = None
    complaint: Optional[str] = None


class BulkStatusUpdate(BaseModel):
    ids: list[str]
    status: Literal["open", "in_review", "escalated", "resolved"]


# ── Response / output schemas ──────────────────────────────────────────────────

class ClassificationResult(BaseModel):
    hazard_type: str
    severity: str
    department: str
    summary: str
    complaint_letter: str
    confidence: Optional[str] = "high"

    @field_validator("hazard_type")
    @classmethod
    def validate_hazard_type(cls, v: str) -> str:
        v = v.lower().strip()
        return v if v in VALID_HAZARD_TYPES else "other"

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        v = v.lower().strip()
        return v if v in VALID_SEVERITIES else "medium"


class ReportResponse(BaseModel):
    id: str
    user_id: Optional[str]
    photo_url: str
    lat: float
    lng: float
    hazard_type: Optional[str]
    severity: Optional[str]
    department: Optional[str]
    summary: Optional[str]
    complaint: Optional[str]
    upvotes: int = 0
    status: str = "open"
    created_at: Optional[str]
    resolved_at: Optional[str]
    distance_km: Optional[float] = None  # populated by nearby endpoint


class AdminStatsResponse(BaseModel):
    open: int
    in_review: int
    escalated: int
    resolved: int
    avg_resolution_hours: Optional[float]


# ── Output sanitizer ───────────────────────────────────────────────────────────

def sanitize_classification(raw: dict) -> ClassificationResult:
    """
    Coerce raw dict from Gemini into a valid ClassificationResult.
    Fixes common issues: wrong keys, mixed case, extra fields.
    """
    from app.utils.fallback import DEPARTMENT_MAP, SAFE_DEFAULT_RESPONSE

    hazard = str(raw.get("hazard_type", "other")).lower().strip()
    if hazard not in VALID_HAZARD_TYPES:
        hazard = "other"

    severity = str(raw.get("severity", "medium")).lower().strip()
    if severity not in VALID_SEVERITIES:
        severity = "medium"

    department = raw.get("department") or DEPARTMENT_MAP.get(hazard, "Municipal Authority")
    summary = raw.get("summary") or "Environmental hazard detected."
    letter = raw.get("complaint_letter") or raw.get("complaint") or SAFE_DEFAULT_RESPONSE["complaint_letter"]
    confidence = raw.get("confidence", "high")

    return ClassificationResult(
        hazard_type=hazard,
        severity=severity,
        department=str(department),
        summary=str(summary),
        complaint_letter=str(letter),
        confidence=str(confidence),
    )
