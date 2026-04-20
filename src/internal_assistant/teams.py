from __future__ import annotations

from copy import deepcopy
from urllib.parse import urlparse


INCIDENT_FIELD_MAP = {
    "title": "titulo",
    "description": "descripcion",
    "department": "departamento",
    "category": "categoria",
    "affected_system": "sistema",
    "system": "sistema",
    "priority": "prioridad",
    "is_resolved": "resuelta",
    "resolution": "resolucion",
    "impact": "impacto",
    "expected_behavior": "esperado",
    "actual_behavior": "actual",
    "tags": "tags",
}


def coerce_activity_input(text: str | None, value: object | None) -> str:
    if text and text.strip():
        return text.strip()

    if not isinstance(value, dict):
        return ""

    feedback_type = str(value.get("feedback_type", "")).strip().lower()
    if feedback_type == "useful":
        return "util"
    if feedback_type in {"not_useful", "wrong_answer", "solution_failed"}:
        return "no util"

    if str(value.get("action", "")).strip().lower() in {"confirm_incident", "confirm"}:
        return "si"

    lines: list[str] = []
    for key, prefix in INCIDENT_FIELD_MAP.items():
        if key not in value:
            continue
        field_value = value[key]
        if field_value is None or str(field_value).strip() == "":
            continue
        if key == "is_resolved":
            normalized = "si" if bool(field_value) else "no"
            lines.append(f"{prefix}: {normalized}")
            continue
        if isinstance(field_value, list):
            joined = ", ".join(str(item) for item in field_value if str(item).strip())
            if joined:
                lines.append(f"{prefix}: {joined}")
            continue
        lines.append(f"{prefix}: {field_value}")

    return "\n".join(lines)


def render_manifest(
    template: dict,
    *,
    teams_app_id: str,
    microsoft_app_id: str,
    bot_endpoint: str,
) -> dict:
    manifest = deepcopy(template)
    manifest["id"] = teams_app_id
    bot_host = urlparse(bot_endpoint).hostname
    if not bot_host:
        raise ValueError("BOT_ENDPOINT no es valido")

    for bot in manifest.get("bots", []):
        bot["botId"] = microsoft_app_id

    valid_domains = set(manifest.get("validDomains", []))
    valid_domains.add(bot_host)
    manifest["validDomains"] = sorted(valid_domains)
    return manifest
