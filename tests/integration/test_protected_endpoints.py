from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient


def test_custom_incidents_write_requires_shared_secret(app_paths, load_module, monkeypatch):
    module = load_module("custom_incidents_local_main", app_paths["custom_incidents"])
    module.app.dependency_overrides[module.get_session] = lambda: None
    client = TestClient(module.app)

    response = client.post(
        "/incidents",
        json={
            "title": "Error",
            "description": "Detalle",
            "department": "Seguridad",
            "category": "accesos",
            "affected_system": "SafeGate",
            "is_resolved": True,
        },
    )

    assert response.status_code == 401


def test_indexer_rebuild_requires_admin_api_key(app_paths, load_module):
    module = load_module("indexer_local_main", app_paths["indexer"])
    module.app.dependency_overrides[module.get_session] = lambda: None
    client = TestClient(module.app)

    response = client.post("/index/rebuild")

    assert response.status_code == 401


def test_indexer_incident_requires_shared_secret(app_paths, load_module):
    module = load_module("indexer_local_main_secret", app_paths["indexer"])
    module.app.dependency_overrides[module.get_session] = lambda: None
    client = TestClient(module.app)

    response = client.post("/index/incident/1")

    assert response.status_code == 401
