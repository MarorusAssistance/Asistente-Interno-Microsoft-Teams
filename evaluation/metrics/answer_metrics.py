from __future__ import annotations

from typing import Any

from evaluation.utils import bool_rate


def compute_answer_metrics(rows: list[dict[str, Any]]) -> dict[str, float]:
    if not rows:
        return {
            "answer_generated": 0.0,
            "answer_contains_required_terms": 0.0,
            "answer_avoids_forbidden_terms": 0.0,
            "answer_mentions_uncertainty_when_needed": 0.0,
            "answer_uses_only_retrieved_context": 0.0,
            "answer_expected_behavior_match": 0.0,
        }
    return {
        "answer_generated": bool_rate(rows, "answer_generated"),
        "answer_contains_required_terms": bool_rate(rows, "answer_contains_required_terms"),
        "answer_avoids_forbidden_terms": bool_rate(rows, "answer_avoids_forbidden_terms"),
        "answer_mentions_uncertainty_when_needed": bool_rate(rows, "answer_mentions_uncertainty_when_needed"),
        "answer_uses_only_retrieved_context": bool_rate(rows, "answer_uses_only_retrieved_context"),
        "answer_expected_behavior_match": bool_rate(rows, "answer_expected_behavior_match"),
    }

