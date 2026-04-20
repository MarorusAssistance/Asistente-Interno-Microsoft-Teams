from __future__ import annotations

import json

import azure.functions as func

from internal_assistant.db import session_scope
from internal_assistant.functions import create_incident, get_incident, list_incidents, update_incident
from internal_assistant.schemas import IncidentCreate, IncidentUpdate
from internal_assistant.security import assert_shared_secret

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="incidents", methods=["GET"])
def incidents(req: func.HttpRequest) -> func.HttpResponse:
    with session_scope() as session:
        payload = [item.model_dump(mode="json") for item in list_incidents(session)]
    return func.HttpResponse(json.dumps(payload, ensure_ascii=False), mimetype="application/json")


@app.route(route="incidents/{incident_id:int}", methods=["GET"])
def incident_detail(req: func.HttpRequest) -> func.HttpResponse:
    incident_id = int(req.route_params["incident_id"])
    with session_scope() as session:
        incident = get_incident(session, incident_id)
    if not incident:
        return func.HttpResponse(status_code=404)
    return func.HttpResponse(incident.model_dump_json(), mimetype="application/json")


@app.route(route="incidents", methods=["POST"])
def incident_create(req: func.HttpRequest) -> func.HttpResponse:
    if not assert_shared_secret(req.headers.get("x-app-shared-secret")):
        return func.HttpResponse(status_code=401)
    payload = IncidentCreate.model_validate_json(req.get_body())
    with session_scope() as session:
        created = create_incident(session, payload)
    return func.HttpResponse(created.model_dump_json(), mimetype="application/json", status_code=201)


@app.route(route="incidents/{incident_id:int}", methods=["PATCH"])
def incident_update(req: func.HttpRequest) -> func.HttpResponse:
    if not assert_shared_secret(req.headers.get("x-app-shared-secret")):
        return func.HttpResponse(status_code=401)
    incident_id = int(req.route_params["incident_id"])
    payload = IncidentUpdate.model_validate_json(req.get_body())
    with session_scope() as session:
        updated = update_incident(session, incident_id, payload)
    if not updated:
        return func.HttpResponse(status_code=404)
    return func.HttpResponse(updated.model_dump_json(), mimetype="application/json")
