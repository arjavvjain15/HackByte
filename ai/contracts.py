from typing import Literal, Optional, TypeAlias

from pydantic import BaseModel, Field


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
DepartmentType: TypeAlias = Literal[
    "Municipal Sanitation",
    "EPA",
    "Public Works",
    "Parks Department",
    "Drainage Authority",
]
PriorityLevel: TypeAlias = Literal["high", "medium", "low"]
ConfidenceLevel: TypeAlias = Literal["high", "low"]


class ClassificationResources(BaseModel):
    workers: int = Field(ge=1)
    vehicles: list[str] = Field(default_factory=list)
    estimated_time: str
    priority: PriorityLevel


class ClassificationResult(BaseModel):
    hazard_type: HazardType
    severity: SeverityLevel
    department: DepartmentType
    summary: str
    complaint_letter: str
    resources: ClassificationResources
    confidence: Optional[ConfidenceLevel] = None
