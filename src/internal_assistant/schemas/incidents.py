from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class IncidentBase(BaseModel):
    title: str
    description: str
    department: str
    category: str
    affected_system: str
    priority: str | None = None
    status: str = "open"
    is_resolved: bool
    resolution: str | None = None
    impact: str | None = None
    expected_behavior: str | None = None
    actual_behavior: str | None = None
    tags: list[str] = Field(default_factory=list)
    created_by: str | None = None
    source: str = "custom_incidents_api"
    source_url: str | None = None

    @model_validator(mode="after")
    def validate_resolution_fields(self):
        if not self.is_resolved:
            required = [self.impact, self.expected_behavior, self.actual_behavior]
            if any(not value for value in required):
                raise ValueError("Las incidencias no resueltas requieren impact, expected_behavior y actual_behavior")
        return self


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    department: str | None = None
    category: str | None = None
    affected_system: str | None = None
    priority: str | None = None
    status: str | None = None
    is_resolved: bool | None = None
    resolution: str | None = None
    impact: str | None = None
    expected_behavior: str | None = None
    actual_behavior: str | None = None
    tags: list[str] | None = None
    source_url: str | None = None


class IncidentRead(IncidentBase):
    id: int
    external_id: str
    created_at: datetime
    resolved_at: datetime | None = None
    updated_at: datetime

    model_config = {"from_attributes": True}
