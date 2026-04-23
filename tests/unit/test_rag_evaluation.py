from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from evaluation.judges import HeuristicJudge, MockJudge
from evaluation.metrics import (
    compute_abstention_metrics,
    compute_citation_metrics,
    compute_retrieval_metrics,
)
from evaluation.runners import run_ablation_eval, run_answer_eval, run_full_eval
from evaluation.types import EvaluationQuestion
from evaluation.utils import load_questions
from internal_assistant.models import Document, Incident
from internal_assistant.rag import RetrievedChunk
from internal_assistant.schemas import ChatResponse, SourceSnippet


ROOT = Path(__file__).resolve().parents[2]


class FakeSession:
    def __init__(self, *, documents=None, incidents=None):
        self.documents = set(documents or [])
        self.incidents = dict(incidents or {})

    def get(self, model, identifier):
        if model is Document:
            return object() if identifier in self.documents else None
        if model is Incident and identifier in self.incidents:
            return SimpleNamespace(is_resolved=self.incidents[identifier])
        return None


class FakeEvalService:
    def __init__(self, session, llm_provider=None):
        self.session = session

    def retrieve(self, message, retrieval_config=None):
        return [
            RetrievedChunk(
                chunk_id=1,
                source_type="document",
                source_id=1,
                content="LogiCore ERP requiere trazabilidad operativa y evidencia documentada.",
                metadata={"title": "Control operativo", "source_url": "https://example/doc/1"},
                final_score=0.91,
            )
        ]

    def simulate_chat(self, request, *, state=None, retrieval_config=None):
        response = ChatResponse(
            conversation_id=request.conversation_id or 1,
            answer="LogiCore ERP requiere trazabilidad operativa y evidencia documentada.",
            sources=[
                SourceSnippet(
                    source_type="document",
                    source_id=1,
                    title="Control operativo",
                    source_url="https://example/doc/1",
                    excerpt="LogiCore ERP requiere trazabilidad operativa",
                    chunk_id=1,
                )
            ],
            related_incidents=[],
            needs_clarification=False,
            clarification_attempt=0,
            should_offer_incident=False,
            fallback_text="LogiCore ERP requiere trazabilidad operativa y evidencia documentada.",
        )
        meta = {
            "retrieved": self.retrieve(request.message, retrieval_config=retrieval_config),
            "decision": SimpleNamespace(used_chunk_ids=[1]),
            "context_chunks": [{"chunk_id": 1, "content": "LogiCore ERP requiere trazabilidad operativa y evidencia documentada."}],
            "latency_ms": 5,
        }
        return response, dict(state or {}), meta


class FakeMultiTurnService:
    def __init__(self, session, llm_provider=None):
        self.session = session

    def retrieve(self, message, retrieval_config=None):
        return []

    def simulate_chat(self, request, *, state=None, retrieval_config=None):
        current = dict(state or {})
        step = int(current.get("step", 0))
        if step < 2:
            response = ChatResponse(
                conversation_id=request.conversation_id or 1,
                answer="Necesito un poco mas de detalle para responder con seguridad.",
                sources=[],
                related_incidents=[],
                needs_clarification=True,
                clarification_attempt=step + 1,
                should_offer_incident=False,
                fallback_text="Necesito un poco mas de detalle para responder con seguridad.",
            )
            current["step"] = step + 1
            meta = {"retrieved": [], "decision": SimpleNamespace(used_chunk_ids=[]), "context_chunks": [], "latency_ms": 4}
            return response, current, meta

        response = ChatResponse(
            conversation_id=request.conversation_id or 1,
            answer="No tengo evidencia suficiente en el indice para responder con seguridad. Si quieres, puedo ayudarte a registrar una incidencia no resuelta.",
            sources=[],
            related_incidents=[],
            needs_clarification=False,
            clarification_attempt=2,
            should_offer_incident=True,
            fallback_text="No tengo evidencia suficiente en el indice para responder con seguridad. Si quieres, puedo ayudarte a registrar una incidencia no resuelta.",
        )
        current["step"] = step + 1
        meta = {"retrieved": [], "decision": SimpleNamespace(used_chunk_ids=[]), "context_chunks": [], "latency_ms": 6}
        return response, current, meta


def _write_dataset(path: Path, payload: list[dict]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_eval_datasets_load_with_expected_minimums():
    questions = load_questions(ROOT / "evaluation" / "datasets" / "rag_eval_questions.json")
    adversarial = load_questions(ROOT / "evaluation" / "datasets" / "adversarial_questions.json")

    assert len(questions) >= 60
    assert len(adversarial) >= 20
    assert sum(1 for item in questions if item.category == "ambigua") >= 2
    assert any(item.follow_up_messages for item in questions)


def test_eval_question_schema_rejects_non_composite_source_ids():
    with pytest.raises(ValueError, match="expected_source_ids"):
        EvaluationQuestion.model_validate(
            {
                "id": "bad-001",
                "question": "Pregunta",
                "category": "operaciones",
                "expected_behavior": "answer_with_sources",
                "expected_source_ids": ["1"],
            }
        )


def test_retrieval_metrics_compute_hit_at_k_and_mrr():
    rows = [
        {
            "expected_source_ids": ["document:1"],
            "expected_source_types": ["document"],
            "retrieved_source_ids": ["document:1", "document:2"],
            "retrieved_source_types": ["document"],
            "top_score": 0.9,
            "latency_ms": 10,
        },
        {
            "expected_source_ids": ["incident:3"],
            "expected_source_types": ["incident"],
            "retrieved_source_ids": ["document:2", "incident:3"],
            "retrieved_source_types": ["document", "incident"],
            "top_score": 0.7,
            "latency_ms": 20,
        },
    ]

    metrics = compute_retrieval_metrics(rows)

    assert metrics["hit_at_1"] == 0.5
    assert metrics["hit_at_3"] == 1.0
    assert metrics["hit_at_5"] == 1.0
    assert metrics["mrr"] == pytest.approx(0.75)


def test_citation_and_abstention_metrics_work():
    rows = [
        {
            "expected_behavior": "answer_with_sources",
            "citation_present": True,
            "citation_source_validity": True,
            "citation_coverage": True,
            "unsupported_answer": False,
            "actual_behavior": "answer_with_sources",
        },
        {
            "expected_behavior": "abstain_and_offer_incident_registration",
            "actual_behavior": "abstain_and_offer_incident_registration",
            "requires_clarification": False,
        },
        {
            "expected_behavior": "ask_clarification",
            "actual_behavior": "ask_clarification",
            "requires_clarification": True,
        },
    ]

    citation_metrics = compute_citation_metrics(rows)
    abstention_metrics = compute_abstention_metrics(rows)

    assert citation_metrics["citation_coverage_rate"] == 1.0
    assert abstention_metrics["abstention_precision"] == 1.0
    assert abstention_metrics["clarification_rate_when_required"] == 1.0
    assert abstention_metrics["incident_registration_offer_rate"] == 1.0


def test_heuristic_judge_detects_missing_sources_and_required_terms():
    session = FakeSession(documents={1}, incidents={1: True})
    judge = HeuristicJudge(session)
    turn = EvaluationQuestion.model_validate(
        {
            "id": "eval-test",
            "question": "Como se gestiona en LogiCore ERP",
            "category": "operaciones",
            "expected_behavior": "answer_with_sources",
            "expected_source_types": ["document"],
            "expected_source_ids": ["document:1"],
            "must_include_terms": ["LogiCore ERP"],
        }
    )
    expanded = load_questions(ROOT / "evaluation" / "datasets" / "rag_eval_questions.json")[0]
    expanded_turn = SimpleNamespace(
        scenario_id=turn.id,
        turn_id=f"{turn.id}:t0",
        category=turn.category,
        message=turn.question,
        expected_behavior=turn.expected_behavior,
        expected_source_types=turn.expected_source_types,
        expected_source_ids=turn.expected_source_ids,
        expected_answer_summary=turn.expected_answer_summary,
        must_include_terms=turn.must_include_terms,
        must_not_include_terms=turn.must_not_include_terms,
        requires_clarification=turn.requires_clarification,
        should_create_incident=turn.should_create_incident,
        turn_index=0,
    )

    response = ChatResponse(
        conversation_id=1,
        answer="LogiCore ERP requiere trazabilidad operativa.",
        sources=[],
        related_incidents=[],
        fallback_text="LogiCore ERP requiere trazabilidad operativa.",
    )
    verdict = judge.judge(
        expanded_turn,
        response,
        {
            "retrieved": [
                RetrievedChunk(
                    chunk_id=1,
                    source_type="document",
                    source_id=1,
                    content="LogiCore ERP requiere trazabilidad operativa.",
                    metadata={},
                    final_score=0.9,
                )
            ],
            "decision": SimpleNamespace(used_chunk_ids=[1]),
            "context_chunks": [{"chunk_id": 1, "content": "LogiCore ERP requiere trazabilidad operativa."}],
        },
    )

    assert verdict["answer_contains_required_terms"] is True
    assert verdict["citation_present"] is False
    assert verdict["answer_expected_behavior_match"] is True


def test_mock_judge_returns_stable_shape():
    judge = MockJudge()
    turn = SimpleNamespace(expected_behavior="answer_with_sources")
    response = ChatResponse(conversation_id=1, answer="Respuesta", sources=[], related_incidents=[], fallback_text="Respuesta")
    verdict = judge.judge(turn, response, {})

    assert set(verdict) >= {
        "actual_behavior",
        "answer_generated",
        "answer_contains_required_terms",
        "answer_expected_behavior_match",
    }


def test_run_ablation_eval_returns_all_configs(tmp_path):
    dataset = [
        {
            "id": "eval-one",
            "question": "Como se controla un pedido intercentro en LogiCore ERP",
            "category": "operaciones",
            "expected_behavior": "answer_with_sources",
            "expected_source_types": ["document"],
            "expected_source_ids": ["document:1"],
            "expected_answer_summary": "",
            "must_include_terms": ["LogiCore ERP"],
            "must_not_include_terms": [],
            "requires_clarification": False,
            "should_create_incident": False,
            "follow_up_messages": [],
        }
    ]
    dataset_path = tmp_path / "eval.json"
    _write_dataset(dataset_path, dataset)

    report = run_ablation_eval(
        dataset_path=dataset_path,
        output_dir=tmp_path,
        provider_name="mock",
        session=FakeSession(documents={1}),
        include_answer_eval=True,
        write_reports=False,
        service_class=FakeEvalService,
    )

    names = {row["config_name"] for row in report["aggregate_metrics"]["comparison"]}
    assert names == {
        "vector_only",
        "text_only",
        "hybrid_default",
        "hybrid_text_heavier",
        "hybrid_vector_heavier",
        "hybrid_top_8",
    }


def test_run_answer_eval_handles_multiturn_sequence(tmp_path):
    dataset = [
        {
            "id": "eval-multi",
            "question": "No puedo cerrar la operacion",
            "category": "ambigua",
            "expected_behavior": "ask_clarification",
            "expected_source_types": [],
            "expected_source_ids": [],
            "expected_answer_summary": "",
            "must_include_terms": [],
            "must_not_include_terms": [],
            "requires_clarification": True,
            "should_create_incident": False,
            "follow_up_messages": [
                {
                    "message": "Sigue fallando y no tengo el sistema exacto",
                    "expected_behavior": "ask_clarification",
                    "expected_source_types": [],
                    "expected_source_ids": [],
                    "expected_answer_summary": "",
                    "must_include_terms": [],
                    "must_not_include_terms": [],
                    "requires_clarification": True,
                    "should_create_incident": False,
                },
                {
                    "message": "No tengo mas detalle, quiero dejar constancia",
                    "expected_behavior": "abstain_and_offer_incident_registration",
                    "expected_source_types": [],
                    "expected_source_ids": [],
                    "expected_answer_summary": "",
                    "must_include_terms": [],
                    "must_not_include_terms": [],
                    "requires_clarification": False,
                    "should_create_incident": True,
                },
            ],
        }
    ]
    dataset_path = tmp_path / "multi.json"
    _write_dataset(dataset_path, dataset)

    report = run_answer_eval(
        dataset_path=dataset_path,
        output_dir=tmp_path,
        provider_name="mock",
        session=FakeSession(),
        write_reports=False,
        service_class=FakeMultiTurnService,
    )

    behaviors = [row["actual_behavior"] for row in report["per_question_results"]]
    assert behaviors == [
        "ask_clarification",
        "ask_clarification",
        "abstain_and_offer_incident_registration",
    ]


def test_run_full_eval_with_mock_provider_does_not_use_openai(tmp_path, monkeypatch):
    dataset = [
        {
            "id": "eval-one",
            "question": "Como se controla un pedido intercentro en LogiCore ERP",
            "category": "operaciones",
            "expected_behavior": "answer_with_sources",
            "expected_source_types": ["document"],
            "expected_source_ids": ["document:1"],
            "expected_answer_summary": "",
            "must_include_terms": ["LogiCore ERP"],
            "must_not_include_terms": [],
            "requires_clarification": False,
            "should_create_incident": False,
            "follow_up_messages": [],
        }
    ]
    dataset_path = tmp_path / "eval.json"
    _write_dataset(dataset_path, dataset)

    class ExplodingOpenAIProvider:
        def __init__(self, *args, **kwargs):
            raise AssertionError("No deberia instanciar OpenAIProvider en modo mock")

    monkeypatch.setattr("evaluation.utils.OpenAIProvider", ExplodingOpenAIProvider)

    report = run_full_eval(
        dataset_path=dataset_path,
        output_dir=tmp_path,
        provider_name="mock",
        include_adversarial=False,
        include_ablation=False,
        session=FakeSession(documents={1}),
        write_reports=False,
        service_class=FakeEvalService,
    )

    assert report["summary"]["Questions evaluated"] == 1
    assert report["aggregate_metrics"]["retrieval"]["hit_at_5"] == 1.0
