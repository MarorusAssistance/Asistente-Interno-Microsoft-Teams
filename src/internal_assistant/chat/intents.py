from __future__ import annotations


def detect_intent(message: str, conversation_state: dict | None = None) -> str:
    normalized = message.strip().lower()
    conversation_state = conversation_state or {}

    if conversation_state.get("offer_incident") and normalized in {"si", "sí", "vale", "de acuerdo", "adelante"}:
        return "register_incident"

    if conversation_state.get("pending_incident_draft"):
        if normalized in {"si", "sí", "confirmo", "confirmar"}:
            return "confirm_incident"
        return "register_incident"

    if normalized.startswith("util") or normalized.startswith("útil"):
        return "feedback"
    if normalized.startswith("no util") or normalized.startswith("no útil"):
        return "feedback"
    if any(token in normalized for token in ["ticket", "incidencia", "registrar", "abrir caso", "abrir incidencia"]):
        return "register_incident"
    if any(token in normalized for token in ["aclaro", "me refiero", "en realidad", "sobre ", "del sistema "]):
        return "clarification"
    return "question_answering"
