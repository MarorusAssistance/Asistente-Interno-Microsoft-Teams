from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from internal_assistant.models import Incident
from internal_assistant.schemas.incidents import IncidentCreate, IncidentRead, IncidentUpdate


def _build_external_id(session: Session) -> str:
    count = session.scalar(select(Incident.id).order_by(Incident.id.desc()).limit(1))
    next_id = (count or 0) + 1
    return f"INC-{next_id:05d}"


def list_incidents(session: Session) -> list[IncidentRead]:
    incidents = session.execute(select(Incident).order_by(Incident.created_at.desc())).scalars().all()
    return [IncidentRead.model_validate(item) for item in incidents]


def get_incident(session: Session, incident_id: int) -> IncidentRead | None:
    incident = session.get(Incident, incident_id)
    return IncidentRead.model_validate(incident) if incident else None


def create_incident(session: Session, payload: IncidentCreate) -> IncidentRead:
    incident = Incident(
        external_id=_build_external_id(session),
        **payload.model_dump(),
    )
    if incident.is_resolved and incident.status == "open":
        incident.status = "resolved"
        incident.resolved_at = datetime.now(timezone.utc)
    session.add(incident)
    session.commit()
    session.refresh(incident)
    return IncidentRead.model_validate(incident)


def update_incident(session: Session, incident_id: int, payload: IncidentUpdate) -> IncidentRead | None:
    incident = session.get(Incident, incident_id)
    if not incident:
        return None

    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(incident, field_name, value)

    if incident.is_resolved and not incident.resolved_at:
        incident.resolved_at = datetime.now(timezone.utc)
        incident.status = "resolved"

    session.add(incident)
    session.commit()
    session.refresh(incident)
    return IncidentRead.model_validate(incident)
