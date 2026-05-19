from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

import httpx

from internal_assistant.config import get_settings


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RerankResult:
    chunk_id: int
    score: float


class RerankerProvider(Protocol):
    model: str

    def rerank(self, *, query: str, documents: list[dict], top_n: int) -> list[RerankResult]:
        ...


class HttpRerankerProvider:
    def __init__(self, *, base_url: str, model: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def rerank(self, *, query: str, documents: list[dict], top_n: int) -> list[RerankResult]:
        response = httpx.post(
            f"{self.base_url}/rerank",
            json={"query": query, "documents": documents, "top_n": top_n},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        results = []
        for item in payload.get("results") or []:
            results.append(RerankResult(chunk_id=int(item["id"]), score=float(item["score"])))
        return results


def build_default_reranker() -> RerankerProvider | None:
    settings = get_settings()
    if not settings.reranker_enabled:
        return None
    return HttpRerankerProvider(
        base_url=settings.reranker_base_url,
        model=settings.reranker_model,
        timeout_seconds=settings.reranker_timeout_seconds,
    )
