from __future__ import annotations

import pytest

from internal_assistant.chat.incident_draft import build_confirmation_text, extract_incident_fields, missing_fields, validate_draft


def test_extract_incident_fields_and_missing_fields_for_unresolved_ticket():
    message = (
        "titulo: Error SafeGate descripcion: No abre el acceso "
        "departamento: Seguridad categoria: accesos sistema: SafeGate resuelta: no"
    )

    draft = extract_incident_fields(message)

    assert draft["title"].startswith("Error SafeGate")
    assert draft["is_resolved"] is False
    assert "impact" in missing_fields(draft)


def test_validate_draft_requires_unresolved_fields():
    with pytest.raises(ValueError):
        validate_draft(
            {
                "title": "Error",
                "description": "Detalle",
                "department": "Seguridad",
                "category": "accesos",
                "affected_system": "SafeGate",
                "is_resolved": False,
            }
        )


def test_build_confirmation_text_contains_summary():
    summary = build_confirmation_text(
        {
            "title": "Error acceso",
            "description": "No entra",
            "department": "Seguridad",
            "category": "accesos",
            "affected_system": "SafeGate",
            "is_resolved": False,
            "impact": "Turno bloqueado",
        }
    )
    assert "Resumen de la incidencia" in summary
    assert "SafeGate" in summary
