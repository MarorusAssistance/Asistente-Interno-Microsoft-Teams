from __future__ import annotations

from pydantic import BaseModel


class FeedbackCreate(BaseModel):
    conversation_id: int
    message_id: int | None = None
    user_id: str
    feedback_type: str
    comment: str | None = None
