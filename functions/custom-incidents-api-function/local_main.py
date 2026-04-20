from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from internal_assistant.db import get_session
from internal_assistant.functions import create_incident, get_incident, list_incidents, update_incident
from internal_assistant.observability import configure_logging
from internal_assistant.schemas import IncidentCreate, IncidentRead, IncidentUpdate
from internal_assistant.security import verify_shared_secret

configure_logging()
app = FastAPI(title="custom-incidents-api-function", version="0.1.0")
DbSession = Annotated[Session, Depends(get_session)]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "custom-incidents-api-function"}


@app.get("/incidents", response_model=list[IncidentRead])
def incidents(session: DbSession) -> list[IncidentRead]:
    return list_incidents(session)


@app.get("/incidents/{incident_id}", response_model=IncidentRead)
def incident_detail(incident_id: int, session: DbSession) -> IncidentRead:
    incident = get_incident(session, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    return incident


@app.post("/incidents", response_model=IncidentRead, dependencies=[Depends(verify_shared_secret)])
def incident_create(payload: IncidentCreate, session: DbSession) -> IncidentRead:
    return create_incident(session, payload)


@app.patch("/incidents/{incident_id}", response_model=IncidentRead, dependencies=[Depends(verify_shared_secret)])
def incident_update(incident_id: int, payload: IncidentUpdate, session: DbSession) -> IncidentRead:
    incident = update_incident(session, incident_id, payload)
    if not incident:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    return incident
