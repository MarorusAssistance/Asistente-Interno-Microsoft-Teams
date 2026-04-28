from __future__ import annotations

from internal_assistant.cards import build_feedback_card, build_incident_confirmation_card, build_sources_card


def test_build_sources_card_includes_sections_for_sources_and_related_incidents():
    card = build_sources_card(
        "Resumen\nProcedimiento validado.\n\nSiguiente paso\nPuedo ampliarlo si lo necesitas.",
        [
            {
                "source_type": "document",
                "source_id": 10,
                "title": "Procedimiento SafeGate",
                "source_url": "https://example/doc/10",
                "excerpt": "Extracto breve",
            }
        ],
        [{"external_id": "INC-0001", "title": "Acceso temporal rechazado", "status": "resolved"}],
    )

    texts = [item.get("text", "") for item in card["body"] if isinstance(item, dict)]
    assert "Fuentes consultadas" in texts
    assert "Incidencias relacionadas" in texts


def test_build_feedback_card_uses_demo_copy():
    card = build_feedback_card()

    assert card["body"][0]["text"] == "Feedback rapido"
    assert card["actions"][0]["title"] == "Me ha ayudado"
    assert card["actions"][1]["title"] == "No me ha ayudado"


def test_build_incident_confirmation_card_mentions_indexing():
    card = build_incident_confirmation_card(
        {
            "external_id": "INC-0007",
            "title": "Ruta aprobada no sincroniza",
            "affected_system": "RutaNexo",
            "status": "open",
        }
    )

    texts = [item.get("text", "") for item in card["body"] if isinstance(item, dict)]
    assert "Incidencia registrada" in texts
    assert any("indice" in text.lower() for text in texts)
