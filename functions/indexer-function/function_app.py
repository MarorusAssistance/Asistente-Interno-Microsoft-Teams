from __future__ import annotations

import json

import azure.functions as func

from internal_assistant.db import session_scope
from internal_assistant.functions import index_document, index_incident, rebuild_index
from internal_assistant.security import assert_admin_api_key, assert_shared_secret

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="index/rebuild", methods=["POST"])
def rebuild(req: func.HttpRequest) -> func.HttpResponse:
    if not assert_admin_api_key(req.headers.get("x-admin-api-key")):
        return func.HttpResponse(status_code=401)
    with session_scope() as session:
        result = rebuild_index(session)
    return func.HttpResponse(json.dumps(result), mimetype="application/json")


@app.route(route="index/incident/{incident_id:int}", methods=["POST"])
def index_one_incident(req: func.HttpRequest) -> func.HttpResponse:
    if not assert_shared_secret(req.headers.get("x-app-shared-secret")):
        return func.HttpResponse(status_code=401)
    incident_id = int(req.route_params["incident_id"])
    with session_scope() as session:
        indexed = index_incident(session, incident_id)
    if indexed == 0:
        return func.HttpResponse(status_code=404)
    return func.HttpResponse(json.dumps({"indexed_chunks": indexed}), mimetype="application/json")


@app.route(route="index/document/{document_id:int}", methods=["POST"])
def index_one_document(req: func.HttpRequest) -> func.HttpResponse:
    if not assert_shared_secret(req.headers.get("x-app-shared-secret")):
        return func.HttpResponse(status_code=401)
    document_id = int(req.route_params["document_id"])
    with session_scope() as session:
        indexed = index_document(session, document_id)
    if indexed == 0:
        return func.HttpResponse(status_code=404)
    return func.HttpResponse(json.dumps({"indexed_chunks": indexed}), mimetype="application/json")
