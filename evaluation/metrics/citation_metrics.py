from __future__ import annotations

from typing import Any

from evaluation.utils import mean


def compute_citation_metrics(rows: list[dict[str, Any]]) -> dict[str, float]:
    eligible = [row for row in rows if row.get("expected_behavior") == "answer_with_sources"]
    if not eligible:
        return {
            "citation_present_rate": 0.0,
            "citation_source_validity_rate": 0.0,
            "citation_coverage_rate": 0.0,
            "unsupported_answer_rate": 0.0,
        }

    return {
        "citation_present_rate": mean([1.0 if row.get("citation_present") else 0.0 for row in eligible]),
        "citation_source_validity_rate": mean([1.0 if row.get("citation_source_validity") else 0.0 for row in eligible]),
        "citation_coverage_rate": mean([1.0 if row.get("citation_coverage") else 0.0 for row in eligible]),
        "unsupported_answer_rate": mean([1.0 if row.get("unsupported_answer") else 0.0 for row in eligible]),
    }

