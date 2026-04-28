from __future__ import annotations

import json
import logging
import sys
from importlib.machinery import EXTENSION_SUFFIXES
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
    payload = {
        "status": "ok",
        "service": "indexer-function",
        "python_version": sys.version,
        "extension_suffixes": EXTENSION_SUFFIXES,
    }
    try:
        import pydantic_core  # noqa: F401

        payload["pydantic_core_import"] = "ok"
    except Exception as exc:  # pragma: no cover - debug route
        payload["pydantic_core_import"] = f"{type(exc).__name__}: {exc}"

    try:
        from internal_assistant.config import get_settings

        payload["settings_import"] = "ok"
        payload["embedding_dimensions"] = get_settings().embedding_dimensions
    except Exception as exc:  # pragma: no cover - debug route
        payload["settings_import"] = f"{type(exc).__name__}: {exc}"

    return func.HttpResponse(json.dumps(payload), mimetype="application/json")


@app.route(route="index/rebuild", methods=["POST"])
def rebuild(req: func.HttpRequest) -> func.HttpResponse:
    from internal_assistant.db import session_scope
    from internal_assistant.functions import rebuild_index
    from internal_assistant.observability import configure_logging
    from internal_assistant.security import assert_admin_api_key

    configure_logging()
    if not assert_admin_api_key(req.headers.get("x-admin-api-key")):
        return func.HttpResponse(status_code=401)
    with session_scope() as session:
        result = rebuild_index(session)
    return func.HttpResponse(json.dumps(result), mimetype="application/json")


@app.route(route="index/incident/{incident_id:int}", methods=["POST"])
def index_one_incident(req: func.HttpRequest) -> func.HttpResponse:
    from internal_assistant.db import session_scope
    from internal_assistant.functions import index_incident
    from internal_assistant.observability import configure_logging
    from internal_assistant.security import assert_shared_secret

    configure_logging()
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
    from internal_assistant.db import session_scope
    from internal_assistant.functions import index_document
    from internal_assistant.observability import configure_logging
    from internal_assistant.security import assert_shared_secret

    configure_logging()
    if not assert_shared_secret(req.headers.get("x-app-shared-secret")):
        return func.HttpResponse(status_code=401)
    document_id = int(req.route_params["document_id"])
    with session_scope() as session:
        indexed = index_document(session, document_id)
    if indexed == 0:
        return func.HttpResponse(status_code=404)
    return func.HttpResponse(json.dumps({"indexed_chunks": indexed}), mimetype="application/json")
