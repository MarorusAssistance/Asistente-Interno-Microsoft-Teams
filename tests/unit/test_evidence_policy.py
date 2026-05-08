from __future__ import annotations

from internal_assistant.chat.evidence import assess_evidence, detect_query_signals
from internal_assistant.rag.retrieval import RetrievedChunk


def chunk(
    *,
    chunk_id: int,
    source_type: str,
    source_id: int,
    system: str,
    title: str = "Fuente",
    final_score: float = 0.9,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        source_type=source_type,
        source_id=source_id,
        content=f"Contenido de {title}",
        metadata={"title": title, "affected_system": system},
        final_score=final_score,
    )


def test_detects_new_issue_signal():
    signals = detect_query_signals("No encuentro solucion para un error nuevo en AlmaTrack WMS")

    assert signals.new_issue is True
    assert signals.mentioned_systems == ["AlmaTrack WMS"]


def test_detects_procedure_request_signal():
    signals = detect_query_signals("Como registro una entrega parcial en LogiCore ERP")

    assert signals.procedure_request is True
    assert signals.mentioned_systems == ["LogiCore ERP"]


def test_detects_dissatisfied_followup_signal():
    signals = detect_query_signals("esa respuesta no me vale, explicamelo mejor")

    assert signals.dissatisfied_followup is True


def test_marks_related_only_for_only_resolved_incidents():
    _, assessment = assess_evidence(
        "No encuentro solucion para un error nuevo en AlmaTrack WMS",
        [
            chunk(chunk_id=1, source_type="incident", source_id=10, system="AlmaTrack WMS"),
            chunk(chunk_id=2, source_type="incident", source_id=11, system="AlmaTrack WMS"),
        ],
    )

    assert assessment.related_only is True
    assert assessment.should_block_answer is True
    assert assessment.reason_code == "new_issue_only_similar_incidents"


def test_marks_system_mismatch():
    _, assessment = assess_evidence(
        "No encuentro solucion para un error nuevo en AlmaTrack WMS",
        [chunk(chunk_id=1, source_type="document", source_id=10, system="SafeGate")],
    )

    assert assessment.system_mismatch is True
    assert assessment.should_block_answer is True
    assert assessment.reason_code == "source_system_mismatch"
