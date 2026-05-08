from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import text
from sqlalchemy.orm import Session

from internal_assistant.models import Chunk, RetrievalLog
from internal_assistant.observability.tracing import set_span_attributes, start_span


class ChunkRepository:
    def __init__(self, session: Session):
        self.session = session

    def delete_by_source(self, source_type: str, source_id: int) -> None:
        self.session.query(Chunk).filter(Chunk.source_type == source_type, Chunk.source_id == source_id).delete()

    def upsert(self, chunk: Chunk) -> Chunk:
        existing = self.session.query(Chunk).filter(Chunk.content_hash == chunk.content_hash).one_or_none()
        if existing:
            existing.content = chunk.content
            existing.embedding = chunk.embedding
            existing.metadata_ = chunk.metadata_
            existing.full_text_tsvector = chunk.full_text_tsvector
            self.session.add(existing)
            self.session.flush()
            return existing

        self.session.add(chunk)
        self.session.flush()
        return chunk

    def vector_search(self, embedding: list[float], limit: int = 15) -> list[dict]:
        with start_span(
            "retrieval.vector_search",
            {"retrieval.vector.limit": limit, "retrieval.embedding_dimensions": len(embedding)},
        ) as span:
            stmt = text(
                """
                SELECT id, source_type, source_id, content, metadata, 1 - (embedding <=> CAST(:embedding AS vector)) AS score
                FROM chunks
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :limit
                """
            )
            rows = self.session.execute(stmt, {"embedding": embedding, "limit": limit}).mappings().all()
            payload = [dict(row) for row in rows]
            scores = [float(row.get("score") or 0.0) for row in payload]
            set_span_attributes(
                span,
                {
                    "retrieval.vector.result_count": len(payload),
                    "retrieval.vector.chunk_ids": [row["id"] for row in payload],
                    "retrieval.vector.score_min": min(scores) if scores else 0.0,
                    "retrieval.vector.score_max": max(scores) if scores else 0.0,
                },
            )
            return payload

    def text_search(self, query: str, limit: int = 15) -> list[dict]:
        with start_span("retrieval.text_search", {"retrieval.text.limit": limit, "query.length": len(query)}) as span:
            stmt = text(
                """
                SELECT id, source_type, source_id, content, metadata,
                       ts_rank_cd(full_text_tsvector, plainto_tsquery('spanish', :query)) AS score
                FROM chunks
                WHERE full_text_tsvector @@ plainto_tsquery('spanish', :query)
                ORDER BY score DESC
                LIMIT :limit
                """
            )
            rows = self.session.execute(stmt, {"query": query, "limit": limit}).mappings().all()
            payload = [dict(row) for row in rows]
            scores = [float(row.get("score") or 0.0) for row in payload]
            set_span_attributes(
                span,
                {
                    "retrieval.text.result_count": len(payload),
                    "retrieval.text.chunk_ids": [row["id"] for row in payload],
                    "retrieval.text.score_min": min(scores) if scores else 0.0,
                    "retrieval.text.score_max": max(scores) if scores else 0.0,
                },
            )
            return payload


class RetrievalLogRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        conversation_id: int | None,
        message_id: int | None,
        query: str,
        detected_intent: str,
        retrieved_chunk_ids: Iterable[int],
        retrieved_source_ids: Iterable[int],
        scores: dict,
        confidence_score: float,
        was_answered: bool,
        tokens_input_estimated: int,
        tokens_output_estimated: int,
        latency_ms: int,
        created_ticket_id: int | None = None,
        answer: str | None = None,
    ) -> RetrievalLog:
        log = RetrievalLog(
            conversation_id=conversation_id,
            message_id=message_id,
            query=query,
            detected_intent=detected_intent,
            retrieved_chunk_ids=list(retrieved_chunk_ids),
            retrieved_source_ids=list(retrieved_source_ids),
            scores=scores,
            confidence_score=confidence_score,
            was_answered=was_answered,
            tokens_input_estimated=tokens_input_estimated,
            tokens_output_estimated=tokens_output_estimated,
            latency_ms=latency_ms,
            created_ticket_id=created_ticket_id,
            answer=answer[:1000] if answer else None,
        )
        self.session.add(log)
        self.session.flush()
        return log
