from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AIScenarioBase(BaseModel):
    domain: str = Field(min_length=1, max_length=100)
    categories: list[str] = Field(default_factory=list)
    app_company: str | None = Field(default=None, max_length=200)
    platform: str | None = Field(default=None, max_length=200)

    pain_points: str = Field(min_length=1)
    problems_to_solve: str = Field(min_length=1)
    expected_outcomes: str = Field(min_length=1)

    implementation_approach: str = Field(min_length=1)
    technical_route: str | None = None
    plan_schedule: str = Field(min_length=1)


class AIScenarioCreate(AIScenarioBase):
    pass


class AIScenarioUpdate(BaseModel):
    domain: str | None = Field(default=None, min_length=1, max_length=100)
    categories: list[str] | None = None
    app_company: str | None = Field(default=None, max_length=200)
    platform: str | None = Field(default=None, max_length=200)

    pain_points: str | None = Field(default=None, min_length=1)
    problems_to_solve: str | None = Field(default=None, min_length=1)
    expected_outcomes: str | None = Field(default=None, min_length=1)

    implementation_approach: str | None = Field(default=None, min_length=1)
    technical_route: str | None = None
    plan_schedule: str | None = Field(default=None, min_length=1)


class AIScenarioOut(AIScenarioBase):
    id: UUID
    status: str
    created_by: str
    created_by_name: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AttachmentOut(BaseModel):
    id: UUID
    scenario_id: UUID
    file_name: str
    content_type: str | None = None
    size: int
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedAIScenarios(BaseModel):
    items: list[AIScenarioOut]
    total: int
    page: int
    page_size: int


class SubmitResponse(BaseModel):
    id: UUID
    status: str


class ErrorResponse(BaseModel):
    detail: str
    extra: dict[str, Any] | None = None

