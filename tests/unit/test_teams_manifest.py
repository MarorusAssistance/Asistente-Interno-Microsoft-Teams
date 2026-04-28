from __future__ import annotations

from internal_assistant.teams import coerce_activity_input, render_manifest


def test_render_manifest_replaces_ids_and_valid_domain():
    template = {
        "id": "placeholder",
        "bots": [{"botId": "placeholder"}],
        "validDomains": [],
    }

    manifest = render_manifest(
        template,
        teams_app_id="teams-app-id",
        microsoft_app_id="bot-app-id",
        bot_endpoint="https://logiassist-demo.azurewebsites.net/api/messages",
    )

    assert manifest["id"] == "teams-app-id"
    assert manifest["bots"][0]["botId"] == "bot-app-id"
    assert manifest["validDomains"] == ["logiassist-demo.azurewebsites.net"]


def test_coerce_activity_input_maps_feedback_and_incident_fields():
    assert coerce_activity_input("", {"feedback_type": "useful"}) == "util"
    assert coerce_activity_input("", {"feedback_type": "not_useful"}) == "no util"

    message = coerce_activity_input(
        "",
        {
            "title": "Error SafeGate",
            "description": "No abre la puerta",
            "affected_system": "SafeGate",
            "is_resolved": False,
        },
    )

    assert "titulo: Error SafeGate" in message
    assert "descripcion: No abre la puerta" in message
    assert "sistema: SafeGate" in message
    assert "resuelta: no" in message
