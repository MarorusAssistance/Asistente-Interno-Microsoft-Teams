from __future__ import annotations


def build_sources_card(answer: str, sources: list[dict], related_incidents: list[dict] | None = None) -> dict:
    source_facts = []
    for source in sources[:5]:
        source_type = "Documento" if source.get("source_type") == "document" else "Incidencia"
        title = source.get("title") or f"{source_type} {source.get('source_id', '')}"
        subtitle = source.get("source_url") or source.get("excerpt", "")
        if len(subtitle) > 140:
            subtitle = subtitle[:137].rstrip() + "..."
        source_facts.append({"title": f"{source_type} {source.get('source_id', '')}", "value": f"{title} - {subtitle}"})

    incident_facts = []
    if related_incidents:
        for incident in related_incidents[:3]:
            incident_facts.append(
                {"title": incident["external_id"], "value": f"{incident['title']} ({incident['status']})"}
            )

    body = [
        {"type": "TextBlock", "text": "Respuesta del asistente", "weight": "Bolder", "size": "Medium"},
        {"type": "TextBlock", "text": answer, "wrap": True},
    ]
    if source_facts:
        body.extend(
            [
                {"type": "TextBlock", "text": "Fuentes consultadas", "weight": "Bolder", "spacing": "Medium"},
                {"type": "FactSet", "facts": source_facts},
            ]
        )
    if incident_facts:
        body.extend(
            [
                {"type": "TextBlock", "text": "Incidencias relacionadas", "weight": "Bolder", "spacing": "Medium"},
                {"type": "FactSet", "facts": incident_facts},
            ]
        )

    return {
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": body,
    }


def build_incident_confirmation_card(incident: dict) -> dict:
    return {
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {"type": "TextBlock", "text": "Incidencia registrada", "weight": "Bolder", "size": "Medium"},
            {
                "type": "TextBlock",
                "text": "El ticket ya esta disponible y se ha enviado al indice para futuras consultas.",
                "wrap": True,
                "spacing": "Small",
            },
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
            {"type": "TextBlock", "text": "Feedback rapido", "weight": "Bolder", "size": "Medium"},
            {"type": "TextBlock", "text": "Te ha resultado util esta respuesta?", "wrap": True},
        ],
        "actions": [
            {"type": "Action.Submit", "title": "Me ha ayudado", "data": {"feedback_type": "useful"}},
            {"type": "Action.Submit", "title": "No me ha ayudado", "data": {"feedback_type": "not_useful"}},
        ],
    }
