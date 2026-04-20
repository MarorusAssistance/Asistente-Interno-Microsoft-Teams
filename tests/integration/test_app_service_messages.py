from __future__ import annotations

from fastapi.testclient import TestClient


async def _fake_process_activity(_activity, _auth_header, _logic):
    return None


def test_api_messages_ignores_unsupported_activity(app_paths, load_module):
    module = load_module("app_service_main_messages_ignore", app_paths["app_service"])
    client = TestClient(module.app)

    response = client.post("/api/messages", json={"type": "conversationUpdate"})

    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


def test_api_messages_calls_adapter_for_message_activity(app_paths, load_module, monkeypatch):
    module = load_module("app_service_main_messages_adapter", app_paths["app_service"])
    monkeypatch.setattr(module.adapter, "process_activity", _fake_process_activity)
    client = TestClient(module.app)

    response = client.post(
        "/api/messages",
        json={
            "type": "message",
            "id": "activity-id",
            "text": "hola",
            "channelId": "msteams",
            "from": {"id": "user-1"},
            "conversation": {"id": "conv-1"},
        },
    )

    assert response.status_code == 200
