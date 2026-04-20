from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from internal_assistant.db import get_session
from internal_assistant.functions import index_document, index_incident, rebuild_index
from internal_assistant.observability import configure_logging
from internal_assistant.security import verify_admin_api_key, verify_shared_secret

configure_logging()
app = FastAPI(title="indexer-function", version="0.1.0")
DbSession = Annotated[Session, Depends(get_session)]


@app.post("/index/rebuild", dependencies=[Depends(verify_admin_api_key)])
def rebuild(session: DbSession) -> dict:
    return rebuild_index(session)


@app.post("/index/incident/{incident_id}", dependencies=[Depends(verify_shared_secret)])
def index_one_incident(incident_id: int, session: DbSession) -> dict:
    indexed = index_incident(session, incident_id)
    if indexed == 0:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada para indexado")
    return {"indexed_chunks": indexed}


@app.post("/index/document/{document_id}", dependencies=[Depends(verify_shared_secret)])
def index_one_document(document_id: int, session: DbSession) -> dict:
    indexed = index_document(session, document_id)
    if indexed == 0:
        raise HTTPException(status_code=404, detail="Documento no encontrado para indexado")
    return {"indexed_chunks": indexed}
