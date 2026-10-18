from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class RequirementUpdate(BaseModel):
    requirement_code: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=8, max_length=2000)
    category: str = Field(default="Functional", max_length=50)
    module: str = Field(default="General", max_length=120)


class RequirementCreate(RequirementUpdate):
    pass


class AnalysisRequest(BaseModel):
    document_id: int = Field(gt=0)
    change_type: Literal["add", "modify", "remove"]
    proposed_change: str = Field(min_length=8, max_length=3000)
    target_requirement_id: int | None = Field(default=None, gt=0)

    @field_validator("proposed_change")
    @classmethod
    def trim_change(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Proposed change cannot be empty")
        return value


class RequirementOut(BaseModel):
    id: int
    requirement_code: str
    description: str
    category: str
    module: str
    source_reference: str

    model_config = {"from_attributes": True}


class DocumentSummary(BaseModel):
    id: int
    filename: str
    requirement_count: int
    extraction_status: str


class AnalysisOut(BaseModel):
    id: int
    document_id: int
    change_type: str
    proposed_change: str
    created_at: datetime
    result: dict[str, Any]
