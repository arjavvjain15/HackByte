from typing import Optional, Literal, TypeAlias
from pydantic import BaseModel, Field, constr

HazardType: TypeAlias = Literal[
    "illegal_dumping",
    "oil_spill",
    "e_waste",
    "water_pollution",
    "blocked_drain",
    "air_pollution",
    "other",
]
SeverityLevel: TypeAlias = Literal["high", "medium", "low"]
ReportStatus: TypeAlias = Literal["open", "in_review", "resolved", "escalated"]
DepartmentType: TypeAlias = Literal[
    "Municipal Sanitation",
    "EPA",
    "Public Works",
    "Parks Department",
    "Drainage Authority",
]
AdminSortType: TypeAlias = Literal["newest", "oldest", "most_upvoted", "highest_severity"]


class PresignRequest(BaseModel):
    filename: Optional[str] = None
    content_type: Optional[str] = None


class ClassifyRequest(BaseModel):
    photo_url: str
    lat: float
    lng: float
    reporter_name: Optional[str] = None


class ReportCreateRequest(BaseModel):
    photo_url: constr(min_length=5, max_length=2048)
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    hazard_type: Optional[HazardType] = None
    severity: Optional[SeverityLevel] = None
    department: Optional[DepartmentType] = None
    summary: Optional[constr(max_length=280)] = None
    complaint_letter: Optional[constr(max_length=8000)] = None


class AdminBulkUpdateRequest(BaseModel):
    ids: list[str]
    status: ReportStatus
