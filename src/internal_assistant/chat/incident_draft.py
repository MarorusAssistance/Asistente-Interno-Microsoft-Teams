from __future__ import annotations

import re

from internal_assistant.schemas.incidents import IncidentCreate


REQUIRED_FIELDS = ["title", "description", "department", "category", "affected_system", "is_resolved"]
UNRESOLVED_REQUIRED_FIELDS = ["impact", "expected_behavior", "actual_behavior"]


def _extract_bool(value: str) -> bool | None:
    normalized = value.lower()
    if any(token in normalized for token in ["no resuelta", "no resuelto", "abierta", "pendiente", "resuelta: no", "resuelto: no"]):
        return False
    if any(token in normalized for token in ["resuelta", "resuelto", "resuelta: si", "resuelta: sí", "resuelto: si", "resuelto: sí"]):
        return True
    return None


def extract_incident_fields(message: str) -> dict:
    patterns = {
        "title": r"titulo[:=]\s*(.+)",
        "description": r"descripcion[:=]\s*(.+)",
        "department": r"(?:departamento|area)[:=]\s*(.+)",
        "category": r"categoria[:=]\s*(.+)",
        "affected_system": r"(?:sistema|affected_system)[:=]\s*(.+)",
        "resolution": r"resolucion[:=]\s*(.+)",
        "impact": r"impacto[:=]\s*(.+)",
        "expected_behavior": r"(?:expected_behavior|esperado)[:=]\s*(.+)",
        "actual_behavior": r"(?:actual_behavior|actual)[:=]\s*(.+)",
        "priority": r"prioridad[:=]\s*(.+)",
        "tags": r"tags[:=]\s*(.+)",
    }
    extracted: dict = {}
    for field_name, pattern in patterns.items():
        match = re.search(pattern, message, flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            extracted[field_name] = [item.strip() for item in value.split(",")] if field_name == "tags" else value

    is_resolved = _extract_bool(message)
    if is_resolved is not None:
        extracted["is_resolved"] = is_resolved

    return extracted


def missing_fields(draft: dict) -> list[str]:
    pending = [field for field in REQUIRED_FIELDS if field not in draft or draft.get(field) in (None, "", [])]
    if "is_resolved" in draft and draft["is_resolved"] is False:
        pending.extend(
            field for field in UNRESOLVED_REQUIRED_FIELDS if field not in draft or draft.get(field) in (None, "", [])
        )
    return pending


def build_confirmation_text(draft: dict) -> str:
    lines = [
        "Resumen de la incidencia:",
        f"- Titulo: {draft.get('title', '-')}",
        f"- Descripcion: {draft.get('description', '-')}",
        f"- Departamento: {draft.get('department', '-')}",
        f"- Categoria: {draft.get('category', '-')}",
        f"- Sistema: {draft.get('affected_system', '-')}",
        f"- Resuelta: {'si' if draft.get('is_resolved') else 'no'}",
    ]
    if draft.get("priority"):
        lines.append(f"- Prioridad: {draft['priority']}")
    if draft.get("resolution"):
        lines.append(f"- Resolucion: {draft['resolution']}")
    if draft.get("impact"):
        lines.append(f"- Impacto: {draft['impact']}")
    lines.append("Responde 'si' para confirmar o envia correcciones con el formato campo: valor.")
    return "\n".join(lines)


def validate_draft(draft: dict) -> IncidentCreate:
    return IncidentCreate.model_validate(draft)
