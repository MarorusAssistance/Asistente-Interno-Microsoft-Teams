from __future__ import annotations

from types import SimpleNamespace

from internal_assistant.rag.chunking import build_chunks_for_document, build_chunks_for_incident


def test_document_chunking_creates_multiple_chunks_for_long_content():
    document = SimpleNamespace(
        title="Manual de operaciones",
        department="Operaciones",
        affected_system="LogiCore ERP",
        tags=["operaciones"],
        source_url="https://example.local/doc",
        content="\n".join([f"Parrafo largo {idx} " + ("texto " * 40) for idx in range(8)]),
    )

    chunks = build_chunks_for_document(document)

    assert len(chunks) >= 2
    assert chunks[0].chunk_index == 0
    assert all(chunk.content_hash for chunk in chunks)


def test_incident_chunking_keeps_single_chunk_for_short_ticket():
    incident = SimpleNamespace(
        title="Acceso SafeGate",
        description="No puedo acceder al portal.",
        affected_system="SafeGate",
        status="open",
        resolution=None,
        impact="Afecta al turno de mañana",
        expected_behavior="Debe permitir acceder",
        actual_behavior="Muestra acceso denegado",
        department="Seguridad",
        tags=["seguridad"],
        source_url=None,
        is_resolved=False,
    )

    chunks = build_chunks_for_incident(incident)

    assert len(chunks) == 1
    assert "SafeGate" in chunks[0].content
