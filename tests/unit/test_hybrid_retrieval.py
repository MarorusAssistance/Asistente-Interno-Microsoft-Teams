from __future__ import annotations

from internal_assistant.rag.retrieval import HybridRetriever


class StubChunkRepository:
    def vector_search(self, embedding, limit=15):
        return [
            {"id": 1, "source_type": "document", "source_id": 10, "content": "alpha", "metadata": {"title": "Doc A"}, "score": 0.9},
            {"id": 2, "source_type": "incident", "source_id": 20, "content": "beta", "metadata": {"title": "Inc B"}, "score": 0.5},
        ]

    def text_search(self, query, limit=15):
        return [
            {"id": 2, "source_type": "incident", "source_id": 20, "content": "beta", "metadata": {"title": "Inc B"}, "score": 0.8},
            {"id": 3, "source_type": "document", "source_id": 30, "content": "gamma", "metadata": {"title": "Doc C"}, "score": 0.4},
        ]


def test_hybrid_retrieval_combines_scores_and_orders_top_results():
    retriever = HybridRetriever.__new__(HybridRetriever)
    retriever.chunk_repository = StubChunkRepository()

    results = retriever.search("consulta", [0.1] * 512, limit=3)

    assert [item.chunk_id for item in results] == [1, 2, 3]
    assert results[0].final_score >= results[1].final_score >= results[2].final_score
