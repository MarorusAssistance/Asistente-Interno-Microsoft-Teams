from __future__ import annotations


def build_sources_card(answer: str, sources: list[dict], related_incidents: list[dict] | None = None) -> dict:
    facts = []
    for source in sources[:5]:
        subtitle = source.get("source_url") or source.get("excerpt", "")[:120]
        facts.append({"title": source["title"], "value": subtitle})

    if related_incidents:
        for incident in related_incidents[:3]:
            facts.append({"title": incident["external_id"], "value": incident["title"]})

    return {
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {"type": "TextBlock", "text": "Respuesta del asistente", "weight": "Bolder", "size": "Medium"},
            {"type": "TextBlock", "text": answer, "wrap": True},
            {"type": "FactSet", "facts": facts},
        ],
    }


def build_incident_confirmation_card(incident: dict) -> dict:
    return {
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {"type": "TextBlock", "text": "Incidencia creada", "weight": "Bolder"},
            {
                "type": "FactSet",
                "facts": [
                    {"title": "Ticket", "value": incident.get("external_id", "")},
                    {"title": "Titulo", "value": incident.get("title", "")},
                    {"title": "Sistema", "value": incident.get("affected_system", "")},
                    {"title": "Estado", "value": incident.get("status", "")},
                ],
            },
        ],
    }


def build_feedback_card() -> dict:
    return {
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {"type": "TextBlock", "text": "Te ha resultado util esta respuesta?", "wrap": True},
        ],
        "actions": [
            {"type": "Action.Submit", "title": "Util", "data": {"feedback_type": "useful"}},
            {"type": "Action.Submit", "title": "No util", "data": {"feedback_type": "not_useful"}},
        ],
    }
