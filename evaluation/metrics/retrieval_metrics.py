from __future__ import annotations

from typing import Any

from evaluation.utils import mean


def _eligible_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("expected_source_ids")]


def _hit_at_k(row: dict[str, Any], k: int) -> float:
    expected = set(row.get("expected_source_ids", []))
    retrieved = list(row.get("retrieved_source_ids", []))[:k]
    return 1.0 if expected.intersection(retrieved) else 0.0


def _coverage_fraction(row: dict[str, Any], k: int) -> float:
    expected = set(row.get("expected_source_ids", []))
    if not expected:
        return 0.0
    retrieved = set(list(row.get("retrieved_source_ids", []))[:k])
    return len(expected.intersection(retrieved)) / len(expected)


def _all_expected_covered(row: dict[str, Any], k: int) -> float:
    expected = set(row.get("expected_source_ids", []))
    if not expected:
        return 0.0
    retrieved = set(list(row.get("retrieved_source_ids", []))[:k])
    return 1.0 if expected.issubset(retrieved) else 0.0


def _mrr(row: dict[str, Any]) -> float:
    expected = set(row.get("expected_source_ids", []))
    for index, source_id in enumerate(row.get("retrieved_source_ids", []), start=1):
        if source_id in expected:
            return 1.0 / index
    return 0.0


def compute_retrieval_metrics(rows: list[dict[str, Any]]) -> dict[str, float]:
    eligible = _eligible_rows(rows)
    if not eligible:
        return {
            "evaluated_questions": 0,
            "hit_at_1": 0.0,
            "hit_at_3": 0.0,
            "hit_at_5": 0.0,
            "recall_at_5": 0.0,
            "mrr": 0.0,
            "average_retrieval_score": 0.0,
            "expected_source_coverage": 0.0,
            "source_type_match_rate": 0.0,
            "average_latency_ms": 0.0,
        }

    return {
        "evaluated_questions": float(len(eligible)),
        "hit_at_1": mean([_hit_at_k(row, 1) for row in eligible]),
        "hit_at_3": mean([_hit_at_k(row, 3) for row in eligible]),
        "hit_at_5": mean([_hit_at_k(row, 5) for row in eligible]),
        "recall_at_5": mean([_coverage_fraction(row, 5) for row in eligible]),
        "mrr": mean([_mrr(row) for row in eligible]),
        "average_retrieval_score": mean([float(row.get("top_score", 0.0)) for row in eligible]),
        "expected_source_coverage": mean([_all_expected_covered(row, 5) for row in eligible]),
        "source_type_match_rate": mean(
            [
                1.0
                if set(row.get("expected_source_types", [])).issubset(set(row.get("retrieved_source_types", [])))
                else 0.0
                for row in eligible
                if row.get("expected_source_types")
            ]
            or [0.0]
        ),
        "average_latency_ms": mean([float(row.get("latency_ms", 0.0)) for row in eligible]),
    }

