from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field, field_validator


ExpectedBehavior = Literal[
    "answer_with_sources",
    "ask_clarification",
    "abstain_and_offer_incident_registration",
    "say_incident_unresolved",
    "say_incident_resolved",
    "reject_prompt_injection",
]

SourceType = Literal["document", "incident"]


class EvaluationQuestionTurn(BaseModel):
    message: str
    expected_behavior: ExpectedBehavior
    expected_source_types: list[SourceType] = Field(default_factory=list)
    expected_source_ids: list[str] = Field(default_factory=list)
    expected_answer_summary: str = ""
    must_include_terms: list[str] = Field(default_factory=list)
    must_not_include_terms: list[str] = Field(default_factory=list)
    requires_clarification: bool = False
    should_create_incident: bool = False

    @field_validator("expected_source_ids")
    @classmethod
    def validate_source_ids(cls, value: list[str]) -> list[str]:
        for item in value:
            if not item.startswith(("document:", "incident:")):
                raise ValueError("expected_source_ids debe usar claves compuestas document:<id> o incident:<id>")
        return value


class EvaluationQuestion(BaseModel):
    id: str
    question: str
    category: str
    expected_behavior: ExpectedBehavior
    expected_source_types: list[SourceType] = Field(default_factory=list)
    expected_source_ids: list[str] = Field(default_factory=list)
    expected_answer_summary: str = ""
    must_include_terms: list[str] = Field(default_factory=list)
    must_not_include_terms: list[str] = Field(default_factory=list)
    requires_clarification: bool = False
    should_create_incident: bool = False
    follow_up_messages: list[EvaluationQuestionTurn] = Field(default_factory=list)

    @field_validator("expected_source_ids")
    @classmethod
    def validate_source_ids(cls, value: list[str]) -> list[str]:
        for item in value:
            if not item.startswith(("document:", "incident:")):
                raise ValueError("expected_source_ids debe usar claves compuestas document:<id> o incident:<id>")
        return value


@dataclass(frozen=True, slots=True)
class ExpandedEvaluationTurn:
    scenario_id: str
    turn_id: str
    category: str
    message: str
    expected_behavior: str
    expected_source_types: list[str]
    expected_source_ids: list[str]
    expected_answer_summary: str
    must_include_terms: list[str]
    must_not_include_terms: list[str]
    requires_clarification: bool
    should_create_incident: bool
    turn_index: int

