from __future__ import annotations

from pathlib import Path
from typing import Any

from internal_assistant.chat.service import ChatService
from internal_assistant.db import session_scope
from internal_assistant.rag import RetrievalConfig

from evaluation.judges import HeuristicJudge, LLMJudge
from evaluation.metrics import compute_abstention_metrics, compute_answer_metrics, compute_citation_metrics
from evaluation.runners.common import answer_recommendations, build_worst_cases, retrieval_config_to_dict, select_examples
from evaluation.utils import (
    build_eval_request,
    estimate_cost,
    load_questions,
    select_provider,
    write_report_bundle,
)


def _ordered_retrieved_source_ids(retrieved) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for item in retrieved:
        key = f"{item.source_type}:{item.source_id}"
        if key not in seen:
            seen.add(key)
            ordered.append(key)
    return ordered


def evaluate_answers(
    session,
    questions,
    *,
    provider_name: str,
    llm_provider,
    retrieval_config: RetrievalConfig,
    use_llm_judge: bool = False,
    judge=None,
    service_class=ChatService,
) -> dict[str, Any]:
    service = service_class(session, llm_provider=llm_provider)
    evaluator = judge or (LLMJudge(session, llm_provider=llm_provider) if use_llm_judge else HeuristicJudge(session))
    rows: list[dict[str, Any]] = []

    total_input_tokens = 0
    total_output_tokens = 0
    total_embedding_tokens = 0

    for index, question in enumerate(questions, start=1):
        state: dict[str, Any] = {}
        conversation_id = 10_000 + index
        from evaluation.utils import expand_question

        expanded_turns = expand_question(question)
        for turn in expanded_turns:
            request = build_eval_request(turn, conversation_id=conversation_id, user_id=f"eval-user-{index}")
            response, state, meta = service.simulate_chat(
                request,
                state=state,
                retrieval_config=retrieval_config,
            )
            verdict = evaluator.judge(turn, response, meta)

            context_tokens = sum(len(str(chunk.get("content", "")).split()) for chunk in meta.get("context_chunks", []))
            input_tokens = len(turn.message.split()) + context_tokens
            output_tokens = len((response.answer or "").split())
            embedding_tokens = len(turn.message.split())
            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
            total_embedding_tokens += embedding_tokens

            row = {
                "scenario_id": turn.scenario_id,
                "turn_id": turn.turn_id,
                "question_id": turn.turn_id,
                "question": turn.message,
                "category": turn.category,
                "expected_behavior": turn.expected_behavior,
                "expected_source_ids": list(turn.expected_source_ids),
                "expected_source_types": list(turn.expected_source_types),
                "expected_answer_summary": turn.expected_answer_summary,
                "requires_clarification": turn.requires_clarification,
                "should_create_incident": turn.should_create_incident,
                "answer": response.answer,
                "sources": [item.model_dump() for item in response.sources],
                "retrieved_source_ids": _ordered_retrieved_source_ids(meta.get("retrieved", [])),
                "retrieved_chunk_ids": [item.chunk_id for item in meta.get("retrieved", [])],
                "latency_ms": meta.get("latency_ms", 0),
                **verdict,
            }
            row.setdefault("issue", "")
            rows.append(row)

    answer_metrics = compute_answer_metrics(rows)
    citation_metrics = compute_citation_metrics(rows)
    abstention_metrics = compute_abstention_metrics(rows)
    average_latency_ms = (
        sum(float(row.get("latency_ms", 0.0)) for row in rows) / len(rows)
        if rows
        else 0.0
    )
    cost_estimate = estimate_cost(
        provider_name=provider_name,
        chat_model=getattr(llm_provider, "settings", None).chat_model if getattr(llm_provider, "settings", None) else "",
        embedding_model=getattr(llm_provider, "settings", None).embedding_model if getattr(llm_provider, "settings", None) else "",
        input_tokens=total_input_tokens,
        output_tokens=total_output_tokens,
        embedding_tokens=total_embedding_tokens,
    )
    return {
        "rows": rows,
        "aggregate_metrics": {
            "answer": answer_metrics,
            "citation": citation_metrics,
            "abstention": abstention_metrics,
        },
        "summary": {
            "Questions evaluated": len(rows),
            "Behavior match": round(float(answer_metrics["answer_expected_behavior_match"]), 4),
            "Citation coverage": round(float(citation_metrics["citation_coverage_rate"]), 4),
            "Abstention precision": round(float(abstention_metrics["abstention_precision"]), 4),
            "Abstention recall": round(float(abstention_metrics["abstention_recall"]), 4),
            "Average latency ms": round(float(average_latency_ms), 2),
        },
        "latency": {"average_latency_ms": average_latency_ms},
        "cost_estimate": cost_estimate,
        "recommendations": answer_recommendations(answer_metrics, citation_metrics, abstention_metrics),
    }


def run_answer_eval(
    *,
    dataset_path: str | Path,
    output_dir: str | Path,
    provider_name: str = "mock",
    retrieval_config: RetrievalConfig | None = None,
    session=None,
    questions=None,
    use_llm_judge: bool = False,
    write_reports: bool = True,
    service_class=ChatService,
) -> dict[str, Any]:
    effective_config = (retrieval_config or RetrievalConfig()).normalized()
    loaded_questions = questions or load_questions(dataset_path)
    owns_session = session is None
    provider = select_provider(provider_name)

    if owns_session:
        with session_scope() as managed_session:
            result = evaluate_answers(
                managed_session,
                loaded_questions,
                provider_name=provider_name,
                llm_provider=provider,
                retrieval_config=effective_config,
                use_llm_judge=use_llm_judge,
                service_class=service_class,
            )
    else:
        result = evaluate_answers(
            session,
            loaded_questions,
            provider_name=provider_name,
            llm_provider=provider,
            retrieval_config=effective_config,
            use_llm_judge=use_llm_judge,
            service_class=service_class,
        )

    payload = {
        "summary": result["summary"],
        "config": {
            "provider": provider_name,
            "dataset_path": str(dataset_path),
            "use_llm_judge": use_llm_judge,
            **retrieval_config_to_dict(effective_config),
        },
        "datasets": {"primary": str(dataset_path)},
        "aggregate_metrics": result["aggregate_metrics"],
        "per_question_results": result["rows"],
        "worst_cases": build_worst_cases(result["rows"]),
        "recommendations": result["recommendations"],
        "latency": result["latency"],
        "cost_estimate": result["cost_estimate"],
    }

    if not write_reports:
        return payload

    json_path, md_path = write_report_bundle(
        report_prefix="answer_eval",
        output_dir=output_dir,
        payload=payload,
        markdown="",
    )
    report_markdown = (
        "# Answer Evaluation Report\n\n"
        "## Summary\n"
        f"- Questions evaluated: {result['summary']['Questions evaluated']}\n"
        f"- Behavior match: {result['summary']['Behavior match']}\n"
        f"- Citation coverage: {result['summary']['Citation coverage']}\n"
        f"- Abstention precision: {result['summary']['Abstention precision']}\n"
        f"- Abstention recall: {result['summary']['Abstention recall']}\n"
        f"- Average latency: {result['summary']['Average latency ms']} ms\n\n"
        "## Worst Cases\n"
    )
    worst_cases = build_worst_cases(result["rows"])
    report_markdown += "| question_id | question | expected_behavior | actual_behavior | issue | retrieved_sources |\n"
    report_markdown += "| --- | --- | --- | --- | --- | --- |\n"
    for row in worst_cases:
        report_markdown += (
            f"| {row['question_id']} | {row['question'].replace('|', '/')} | {row['expected_behavior']} | "
            f"{row['actual_behavior']} | {row['issue'].replace('|', '/')} | {', '.join(row['retrieved_sources'])} |\n"
        )
    report_markdown += "\n## Correct Examples\n"
    for row in select_examples(result["rows"], correct=True):
        report_markdown += f"- `{row['question_id']}` {row['question']}\n"
    report_markdown += "\n## Problematic Examples\n"
    for row in select_examples(result["rows"], correct=False):
        report_markdown += f"- `{row['question_id']}` {row['question']}: {row['issue']}\n"
    report_markdown += "\n## Recommendations\n"
    for item in result["recommendations"]:
        report_markdown += f"- {item}\n"
    md_path.write_text(report_markdown, encoding="utf-8")

    payload["report_paths"] = {"json": str(json_path), "markdown": str(md_path)}
    return payload
