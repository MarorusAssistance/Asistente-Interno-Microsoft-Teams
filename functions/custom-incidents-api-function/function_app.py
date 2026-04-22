from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import azure.functions as func


APP_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = APP_ROOT / "src"
for candidate in (APP_ROOT, SOURCE_ROOT):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

logging.basicConfig(level=logging.INFO)
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({"status": "ok", "service": "custom-incidents-api-function"}),
        mimetype="application/json",
    )


@app.route(route="incidents", methods=["GET"])
def incidents(req: func.HttpRequest) -> func.HttpResponse:
    from internal_assistant.db import session_scope
    from internal_assistant.functions import list_incidents
    from internal_assistant.observability import configure_logging

    configure_logging()
    with session_scope() as session:
        payload = [item.model_dump(mode="json") for item in list_incidents(session)]
    return func.HttpResponse(json.dumps(payload, ensure_ascii=False), mimetype="application/json")


@app.route(route="incidents/{incident_id:int}", methods=["GET"])
def incident_detail(req: func.HttpRequest) -> func.HttpResponse:
    from internal_assistant.db import session_scope
    from internal_assistant.functions import get_incident
    from internal_assistant.observability import configure_logging

    configure_logging()
    incident_id = int(req.route_params["incident_id"])
    with session_scope() as session:
        incident = get_incident(session, incident_id)
    if not incident:
        return func.HttpResponse(status_code=404)
    return func.HttpResponse(incident.model_dump_json(), mimetype="application/json")


@app.route(route="incidents", methods=["POST"])
def incident_create(req: func.HttpRequest) -> func.HttpResponse:
    from internal_assistant.db import session_scope
    from internal_assistant.functions import create_incident
    from internal_assistant.observability import configure_logging
    from internal_assistant.schemas import IncidentCreate
    from internal_assistant.security import assert_shared_secret

    configure_logging()
    if not assert_shared_secret(req.headers.get("x-app-shared-secret")):
        return func.HttpResponse(status_code=401)
    payload = IncidentCreate.model_validate_json(req.get_body())
    with session_scope() as session:
        created = create_incident(session, payload)
    return func.HttpResponse(created.model_dump_json(), mimetype="application/json", status_code=201)


@app.route(route="incidents/{incident_id:int}", methods=["PATCH"])
def incident_update(req: func.HttpRequest) -> func.HttpResponse:
    from internal_assistant.db import session_scope
    from internal_assistant.functions import update_incident
    from internal_assistant.observability import configure_logging
    from internal_assistant.schemas import IncidentUpdate
    from internal_assistant.security import assert_shared_secret

    configure_logging()
    if not assert_shared_secret(req.headers.get("x-app-shared-secret")):
        return func.HttpResponse(status_code=401)
    incident_id = int(req.route_params["incident_id"])
    payload = IncidentUpdate.model_validate_json(req.get_body())
    with session_scope() as session:
        updated = update_incident(session, incident_id, payload)
    if not updated:
        return func.HttpResponse(status_code=404)
    return func.HttpResponse(updated.model_dump_json(), mimetype="application/json")
