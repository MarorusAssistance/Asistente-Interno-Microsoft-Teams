from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from internal_assistant.repositories.retrieval import ChunkRepository


@dataclass(slots=True)
class RetrievedChunk:
    chunk_id: int
    source_type: str
    source_id: int
    content: str
    metadata: dict
    vector_score: float = 0.0
    text_score: float = 0.0
    final_score: float = 0.0


def _normalize(scores: list[float]) -> list[float]:
    if not scores:
        return []
    maximum = max(scores)
    minimum = min(scores)
    if maximum == minimum:
        return [1.0 if maximum > 0 else 0.0 for _ in scores]
    return [(score - minimum) / (maximum - minimum) for score in scores]


class HybridRetriever:
    def __init__(self, session: Session):
        self.chunk_repository = ChunkRepository(session)

    def search(self, query: str, query_embedding: list[float], limit: int = 5) -> list[RetrievedChunk]:
        vector_rows = self.chunk_repository.vector_search(query_embedding, limit=15)
        text_rows = self.chunk_repository.text_search(query, limit=15)

        merged: dict[int, RetrievedChunk] = {}
        for row in vector_rows:
            merged[row["id"]] = RetrievedChunk(
                chunk_id=row["id"],
                source_type=row["source_type"],
                source_id=row["source_id"],
                content=row["content"],
                metadata=row["metadata"] or {},
                vector_score=float(row["score"] or 0.0),
            )

        for row in text_rows:
            existing = merged.get(row["id"])
            if existing:
                existing.text_score = float(row["score"] or 0.0)
            else:
                merged[row["id"]] = RetrievedChunk(
                    chunk_id=row["id"],
                    source_type=row["source_type"],
                    source_id=row["source_id"],
                    content=row["content"],
                    metadata=row["metadata"] or {},
                    text_score=float(row["score"] or 0.0),
                )

        ordered = list(merged.values())
        vector_norm = _normalize([chunk.vector_score for chunk in ordered])
        text_norm = _normalize([chunk.text_score for chunk in ordered])

        for idx, chunk in enumerate(ordered):
            chunk.final_score = 0.70 * vector_norm[idx] + 0.30 * text_norm[idx]

        ordered.sort(key=lambda item: item.final_score, reverse=True)
        return ordered[:limit]
