from __future__ import annotations

from typing import Any

from internal_assistant.schemas import ChatResponse

from evaluation.types import ExpandedEvaluationTurn

from .base import BaseJudge


class MockJudge(BaseJudge):
    def judge(self, turn: ExpandedEvaluationTurn, response: ChatResponse, meta: dict[str, Any]) -> dict[str, Any]:
        actual_behavior = "ask_clarification" if response.needs_clarification else (
            "abstain_and_offer_incident_registration" if response.should_offer_incident else turn.expected_behavior
        )
        return {
            "actual_behavior": actual_behavior,
            "answer_generated": bool(response.answer.strip()),
            "answer_contains_required_terms": True,
            "answer_avoids_forbidden_terms": True,
            "answer_mentions_uncertainty_when_needed": True,
            "answer_uses_only_retrieved_context": True,
            "answer_expected_behavior_match": actual_behavior == turn.expected_behavior,
            "citation_present": bool(response.sources),
            "citation_source_validity": True,
            "citation_coverage": bool(getattr(turn, "expected_source_ids", [])),
            "unsupported_answer": False,
            "is_correct": actual_behavior == turn.expected_behavior,
        }
