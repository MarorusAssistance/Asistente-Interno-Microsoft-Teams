from __future__ import annotations

from dataclasses import dataclass, replace

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


@dataclass(frozen=True, slots=True)
class RetrievalConfig:
    top_k: int = 5
    vector_weight: float = 0.70
    text_weight: float = 0.30
    vector_candidates: int = 15
    text_candidates: int = 15

    def normalized(self) -> "RetrievalConfig":
        top_k = max(1, int(self.top_k))
        vector_candidates = max(top_k, int(self.vector_candidates))
        text_candidates = max(top_k, int(self.text_candidates))
        vector_weight = max(0.0, float(self.vector_weight))
        text_weight = max(0.0, float(self.text_weight))
        total_weight = vector_weight + text_weight
        if total_weight <= 0:
            vector_weight = 0.70
            text_weight = 0.30
            total_weight = 1.0
        return RetrievalConfig(
            top_k=top_k,
            vector_weight=vector_weight / total_weight,
            text_weight=text_weight / total_weight,
            vector_candidates=vector_candidates,
            text_candidates=text_candidates,
        )


DEFAULT_RETRIEVAL_CONFIG = RetrievalConfig()


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

    def search(
        self,
        query: str,
        query_embedding: list[float],
        limit: int | None = None,
        config: RetrievalConfig | None = None,
    ) -> list[RetrievedChunk]:
        effective = (config or DEFAULT_RETRIEVAL_CONFIG).normalized()
        if limit is not None:
            effective = replace(effective, top_k=max(1, int(limit))).normalized()

        vector_rows = self.chunk_repository.vector_search(query_embedding, limit=effective.vector_candidates)
        text_rows = self.chunk_repository.text_search(query, limit=effective.text_candidates)

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
            chunk.final_score = (
                effective.vector_weight * vector_norm[idx] + effective.text_weight * text_norm[idx]
            )

        ordered.sort(key=lambda item: item.final_score, reverse=True)
        return ordered[: effective.top_k]
