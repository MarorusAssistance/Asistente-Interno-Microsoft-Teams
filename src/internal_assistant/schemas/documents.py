from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DocumentRead(BaseModel):
    id: int
    title: str
    document_type: str
    department: str
    affected_system: str | None = None
    content: str
    tags: list[str]
    source_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
