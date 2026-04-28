from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from pathlib import Path
from typing import Any

from internal_assistant.config import get_settings
from internal_assistant.chat.service import ChatService
from internal_assistant.db import session_scope
from internal_assistant.rag import RetrievalConfig

from evaluation.metrics import compute_retrieval_metrics
from evaluation.runners.common import build_worst_cases, retrieval_config_to_dict, retrieval_recommendations, select_examples
from evaluation.utils import (
    expand_questions,
    load_questions,
    retrieved_source_types,
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


def _evaluate_retrieval_question(
    *,
    question,
    provider_name: str,
    retrieval_config: RetrievalConfig,
    service_class,
) -> list[dict[str, Any]]:
    from evaluation.utils import expand_question, select_provider

    with session_scope() as session:
        llm_provider = select_provider(provider_name)
        service = service_class(session, llm_provider=llm_provider)
        rows: list[dict[str, Any]] = []
        for turn in expand_question(question):
            started_at = time.perf_counter()
            retrieved = service.retrieve(turn.message, retrieval_config=retrieval_config)
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            retrieved_keys = _ordered_retrieved_source_ids(retrieved)
            row = {
                "turn_id": turn.turn_id,
                "question_id": turn.turn_id,
                "question": turn.message,
                "category": turn.category,
                "expected_behavior": turn.expected_behavior,
                "expected_source_ids": list(turn.expected_source_ids),
                "expected_source_types": list(turn.expected_source_types),
                "retrieved_chunk_ids": [item.chunk_id for item in retrieved],
                "retrieved_source_ids": retrieved_keys,
                "retrieved_source_types": sorted(retrieved_source_types(retrieved)),
                "top_score": float(retrieved[0].final_score) if retrieved else 0.0,
                "latency_ms": latency_ms,
            }
            row["hit_at_5"] = bool(set(turn.expected_source_ids).intersection(retrieved_keys))
            row["issue"] = "No recupero ninguna fuente esperada" if turn.expected_source_ids and not row["hit_at_5"] else "OK"
            rows.append(row)
        return rows


def evaluate_retrieval(
    session,
    questions,
    *,
    llm_provider,
    retrieval_config: RetrievalConfig,
    service_class=ChatService,
) -> dict[str, Any]:
    service = service_class(session, llm_provider=llm_provider)
    rows: list[dict[str, Any]] = []

    for turn in expand_questions(questions):
        started_at = time.perf_counter()
        retrieved = service.retrieve(turn.message, retrieval_config=retrieval_config)
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        retrieved_keys = _ordered_retrieved_source_ids(retrieved)
        row = {
            "turn_id": turn.turn_id,
            "question_id": turn.turn_id,
            "question": turn.message,
            "category": turn.category,
            "expected_behavior": turn.expected_behavior,
            "expected_source_ids": list(turn.expected_source_ids),
            "expected_source_types": list(turn.expected_source_types),
            "retrieved_chunk_ids": [item.chunk_id for item in retrieved],
            "retrieved_source_ids": retrieved_keys,
            "retrieved_source_types": sorted(retrieved_source_types(retrieved)),
            "top_score": float(retrieved[0].final_score) if retrieved else 0.0,
            "latency_ms": latency_ms,
        }
        row["hit_at_5"] = bool(set(turn.expected_source_ids).intersection(retrieved_keys))
        row["issue"] = "No recupero ninguna fuente esperada" if turn.expected_source_ids and not row["hit_at_5"] else "OK"
        rows.append(row)

    metrics = compute_retrieval_metrics(rows)
    return {
        "rows": rows,
        "aggregate_metrics": metrics,
        "summary": {
            "Questions evaluated": len(rows),
            "Retrieval hit@5": round(float(metrics["hit_at_5"]), 4),
            "MRR": round(float(metrics["mrr"]), 4),
            "Average latency ms": round(float(metrics["average_latency_ms"]), 2),
        },
        "recommendations": retrieval_recommendations(metrics),
    }


def run_retrieval_eval(
    *,
    dataset_path: str | Path,
    output_dir: str | Path,
    provider_name: str = "mock",
    retrieval_config: RetrievalConfig | None = None,
    session=None,
    questions=None,
    max_concurrency: int | None = None,
    write_reports: bool = True,
    service_class=ChatService,
) -> dict[str, Any]:
    effective_config = (retrieval_config or RetrievalConfig()).normalized()
    loaded_questions = questions or load_questions(dataset_path)
    owns_session = session is None
    provider = select_provider(provider_name)
    effective_concurrency = max(1, max_concurrency or get_settings().eval_max_concurrency)

    if owns_session and effective_concurrency > 1:
        with ThreadPoolExecutor(max_workers=effective_concurrency) as executor:
            futures = [
                executor.submit(
                    _evaluate_retrieval_question,
                    question=question,
                    provider_name=provider_name,
                    retrieval_config=effective_config,
                    service_class=service_class,
                )
                for question in loaded_questions
            ]
            rows: list[dict[str, Any]] = []
            for future in as_completed(futures):
                rows.extend(future.result())
        result = {
            "rows": rows,
            "aggregate_metrics": compute_retrieval_metrics(rows),
            "summary": {},
            "recommendations": [],
        }
        result["summary"] = {
            "Questions evaluated": len(rows),
            "Retrieval hit@5": round(float(result["aggregate_metrics"]["hit_at_5"]), 4),
            "MRR": round(float(result["aggregate_metrics"]["mrr"]), 4),
            "Average latency ms": round(float(result["aggregate_metrics"]["average_latency_ms"]), 2),
        }
        result["recommendations"] = retrieval_recommendations(result["aggregate_metrics"])
    elif owns_session:
        with session_scope() as managed_session:
            result = evaluate_retrieval(
                managed_session,
                loaded_questions,
                llm_provider=provider,
                retrieval_config=effective_config,
                service_class=service_class,
            )
    else:
        result = evaluate_retrieval(
            session,
            loaded_questions,
            llm_provider=provider,
            retrieval_config=effective_config,
            service_class=service_class,
        )

    payload = {
        "summary": result["summary"],
        "config": {
            "provider": provider_name,
            "dataset_path": str(dataset_path),
            **retrieval_config_to_dict(effective_config),
        },
        "datasets": {"primary": str(dataset_path)},
        "aggregate_metrics": result["aggregate_metrics"],
        "per_question_results": result["rows"],
        "worst_cases": build_worst_cases(result["rows"]),
        "recommendations": result["recommendations"],
        "latency": {
            "average_latency_ms": result["aggregate_metrics"]["average_latency_ms"],
        },
        "cost_estimate": {
            "provider": provider_name,
            "estimated_usd": 0.0 if provider_name == "mock" else None,
            "note": "La evaluacion de retrieval no genera respuestas; solo usa embeddings.",
        },
    }

    if not write_reports:
        return payload

    markdown = write_report_bundle(
        report_prefix="retrieval_eval",
        output_dir=output_dir,
        payload=payload,
        markdown="",
    )
    json_path, md_path = markdown
    report_markdown = (
        "# Retrieval Evaluation Report\n\n"
        "## Summary\n"
        f"- Questions evaluated: {result['summary']['Questions evaluated']}\n"
        f"- Retrieval hit@5: {result['summary']['Retrieval hit@5']}\n"
        f"- MRR: {result['summary']['MRR']}\n"
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
