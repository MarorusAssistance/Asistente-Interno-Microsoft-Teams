from __future__ import annotations

from sqlalchemy.orm import Session

from internal_assistant.models import Feedback
from internal_assistant.schemas.feedback import FeedbackCreate


class FeedbackRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, payload: FeedbackCreate) -> Feedback:
        feedback = Feedback(**payload.model_dump())
        self.session.add(feedback)
        self.session.flush()
        return feedback
