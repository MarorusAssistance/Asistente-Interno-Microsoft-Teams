from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from internal_assistant.models import Document, Incident


class IncidentRepository:
    def __init__(self, session: Session):
        self.session = session

    def list(self) -> list[Incident]:
        stmt = select(Incident).order_by(Incident.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def get(self, incident_id: int) -> Incident | None:
        return self.session.get(Incident, incident_id)

    def list_related(self, ids: list[int]) -> list[Incident]:
        if not ids:
            return []
        stmt = select(Incident).where(Incident.id.in_(ids))
        return list(self.session.execute(stmt).scalars().all())


class DocumentRepository:
    def __init__(self, session: Session):
        self.session = session

    def list(self) -> list[Document]:
        stmt = select(Document).order_by(Document.updated_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def get(self, document_id: int) -> Document | None:
        return self.session.get(Document, document_id)
