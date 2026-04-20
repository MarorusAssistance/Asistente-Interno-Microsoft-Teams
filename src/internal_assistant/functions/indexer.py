from __future__ import annotations

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from internal_assistant.llm import LLMProvider, build_default_provider
from internal_assistant.models import Chunk, Document, Incident
from internal_assistant.rag.chunking import build_chunks_for_document, build_chunks_for_incident
from internal_assistant.repositories.retrieval import ChunkRepository


def _refresh_tsvector(session: Session, chunk_id: int) -> None:
    session.execute(
        text("UPDATE chunks SET full_text_tsvector = to_tsvector('spanish', content) WHERE id = :chunk_id"),
        {"chunk_id": chunk_id},
    )


def _index_source_chunks(session: Session, source_type: str, source_id: int, payloads, llm_provider: LLMProvider) -> int:
    repository = ChunkRepository(session)
    repository.delete_by_source(source_type, source_id)
    embeddings = llm_provider.embed_texts([payload.content for payload in payloads]) if payloads else []

    for payload, embedding in zip(payloads, embeddings):
        chunk = Chunk(
            source_type=source_type,
            source_id=source_id,
            chunk_index=payload.chunk_index,
            content=payload.content,
            content_hash=payload.content_hash,
            embedding=embedding,
            metadata_=payload.metadata,
            full_text_tsvector=None,
        )
        persisted = repository.upsert(chunk)
        _refresh_tsvector(session, persisted.id)

    session.commit()
    return len(payloads)


def index_document(session: Session, document_id: int, llm_provider: LLMProvider | None = None) -> int:
    provider = llm_provider or build_default_provider()
    document = session.get(Document, document_id)
    if not document:
        return 0
    payloads = build_chunks_for_document(document)
    return _index_source_chunks(session, "document", document.id, payloads, provider)


def index_incident(session: Session, incident_id: int, llm_provider: LLMProvider | None = None) -> int:
    provider = llm_provider or build_default_provider()
    incident = session.get(Incident, incident_id)
    if not incident:
        return 0
    payloads = build_chunks_for_incident(incident)
    return _index_source_chunks(session, "incident", incident.id, payloads, provider)


def rebuild_index(session: Session, llm_provider: LLMProvider | None = None) -> dict:
    provider = llm_provider or build_default_provider()
    session.execute(text("DELETE FROM chunks"))
    session.commit()

    document_count = 0
    incident_count = 0

    for document_id in session.execute(select(Document.id).order_by(Document.id)).scalars().all():
        document_count += index_document(session, document_id, provider)

    for incident_id in session.execute(select(Incident.id).order_by(Incident.id)).scalars().all():
        incident_count += index_incident(session, incident_id, provider)

    stats = session.execute(select(func.count(Chunk.id))).scalar_one()
    return {
        "documents_chunks": document_count,
        "incidents_chunks": incident_count,
        "total_chunks": stats,
    }
