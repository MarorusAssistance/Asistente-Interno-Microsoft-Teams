from __future__ import annotations

from typing import Any

from evaluation.utils import mean


ABSTAIN_BEHAVIORS = {"ask_clarification", "abstain_and_offer_incident_registration"}


def compute_abstention_metrics(rows: list[dict[str, Any]]) -> dict[str, float]:
    if not rows:
        return {
            "abstention_precision": 0.0,
            "abstention_recall": 0.0,
            "false_answer_when_should_abstain": 0.0,
            "unnecessary_abstention_when_answer_exists": 0.0,
            "clarification_rate_when_required": 0.0,
            "incident_registration_offer_rate": 0.0,
        }

    should_abstain = [row for row in rows if row.get("expected_behavior") in ABSTAIN_BEHAVIORS]
    predicted_abstain = [row for row in rows if row.get("actual_behavior") in ABSTAIN_BEHAVIORS]
    true_positive = [row for row in predicted_abstain if row.get("expected_behavior") in ABSTAIN_BEHAVIORS]

    precision = len(true_positive) / len(predicted_abstain) if predicted_abstain else 0.0
    recall = len(true_positive) / len(should_abstain) if should_abstain else 0.0

    clarification_rows = [row for row in rows if row.get("requires_clarification") or row.get("expected_behavior") == "ask_clarification"]
    offer_rows = [row for row in rows if row.get("expected_behavior") == "abstain_and_offer_incident_registration"]

    return {
        "abstention_precision": precision,
        "abstention_recall": recall,
        "false_answer_when_should_abstain": mean(
            [
                1.0
                if row.get("expected_behavior") in ABSTAIN_BEHAVIORS and row.get("actual_behavior") not in ABSTAIN_BEHAVIORS
                else 0.0
                for row in rows
            ]
        ),
        "unnecessary_abstention_when_answer_exists": mean(
            [
                1.0
                if row.get("expected_behavior") not in ABSTAIN_BEHAVIORS and row.get("actual_behavior") in ABSTAIN_BEHAVIORS
                else 0.0
                for row in rows
            ]
        ),
        "clarification_rate_when_required": mean(
            [1.0 if row.get("actual_behavior") == "ask_clarification" else 0.0 for row in clarification_rows] or [0.0]
        ),
        "incident_registration_offer_rate": mean(
            [1.0 if row.get("actual_behavior") == "abstain_and_offer_incident_registration" else 0.0 for row in offer_rows] or [0.0]
        ),
    }
