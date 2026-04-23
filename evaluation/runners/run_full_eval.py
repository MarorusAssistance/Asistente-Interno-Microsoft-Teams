from __future__ import annotations

from pathlib import Path
from typing import Any

from internal_assistant.chat.service import ChatService
from internal_assistant.rag import RetrievalConfig

from evaluation.runners.common import build_worst_cases, select_examples
from evaluation.runners.run_ablation_eval import run_ablation_eval
from evaluation.runners.run_answer_eval import run_answer_eval
from evaluation.runners.run_retrieval_eval import run_retrieval_eval
from evaluation.utils import load_questions, write_report_bundle


def _compute_adversarial_metrics(rows: list[dict[str, Any]]) -> dict[str, float]:
    def rate(category: str) -> float:
        subset = [row for row in rows if row.get("category") == category]
        if not subset:
            return 0.0
        return sum(1.0 if row.get("answer_expected_behavior_match") else 0.0 for row in subset) / len(subset)

    return {
        "injection_rejection_rate": rate("prompt_injection"),
        "secret_request_rejection_rate": rate("secret_request"),
        "out_of_scope_rejection_rate": rate("out_of_scope"),
        "hallucination_request_rejection_rate": rate("hallucination_request"),
    }


def run_full_eval(
    *,
    dataset_path: str | Path,
    output_dir: str | Path,
    provider_name: str = "mock",
    retrieval_config: RetrievalConfig | None = None,
    include_adversarial: bool = False,
    include_ablation: bool = False,
    use_llm_judge: bool = False,
    adversarial_dataset_path: str | Path | None = None,
    session=None,
    write_reports: bool = True,
    service_class=ChatService,
) -> dict[str, Any]:
    effective_config = (retrieval_config or RetrievalConfig()).normalized()

    retrieval_report = run_retrieval_eval(
        dataset_path=dataset_path,
        output_dir=output_dir,
        provider_name=provider_name,
        retrieval_config=effective_config,
        session=session,
        questions=None,
        write_reports=False,
        service_class=service_class,
    )
    answer_report = run_answer_eval(
        dataset_path=dataset_path,
        output_dir=output_dir,
        provider_name=provider_name,
        retrieval_config=effective_config,
        session=session,
        questions=None,
        use_llm_judge=use_llm_judge,
        write_reports=False,
        service_class=service_class,
    )

    adversarial_report = None
    adversarial_metrics: dict[str, float] = {}
    if include_adversarial and adversarial_dataset_path:
        adversarial_report = run_answer_eval(
            dataset_path=adversarial_dataset_path,
            output_dir=output_dir,
            provider_name=provider_name,
            retrieval_config=effective_config,
            session=session,
            questions=None,
            use_llm_judge=use_llm_judge,
            write_reports=False,
            service_class=service_class,
        )
        adversarial_metrics = _compute_adversarial_metrics(adversarial_report["per_question_results"])

    ablation_report = None
    if include_ablation:
        ablation_report = run_ablation_eval(
            dataset_path=dataset_path,
            output_dir=output_dir,
            provider_name=provider_name,
            session=session,
            questions=load_questions(dataset_path),
            include_answer_eval=True,
            write_reports=False,
            service_class=service_class,
        )

    answer_rows = list(answer_report["per_question_results"])
    if adversarial_report:
        answer_rows.extend(adversarial_report["per_question_results"])

    summary = {
        "Questions evaluated": len(answer_report["per_question_results"]),
        "Retrieval hit@5": round(float(retrieval_report["aggregate_metrics"]["hit_at_5"]), 4),
        "MRR": round(float(retrieval_report["aggregate_metrics"]["mrr"]), 4),
        "Citation coverage": round(float(answer_report["aggregate_metrics"]["citation"]["citation_coverage_rate"]), 4),
        "Abstention precision": round(float(answer_report["aggregate_metrics"]["abstention"]["abstention_precision"]), 4),
        "Abstention recall": round(float(answer_report["aggregate_metrics"]["abstention"]["abstention_recall"]), 4),
        "Prompt injection rejection rate": round(float(adversarial_metrics.get("injection_rejection_rate", 0.0)), 4),
        "Average latency": round(float(answer_report["latency"]["average_latency_ms"]), 2),
    }

    recommendations = list(answer_report["recommendations"])
    if ablation_report and ablation_report["recommendations"]:
        recommendations.extend(ablation_report["recommendations"][:1])

    payload = {
        "summary": summary,
        "config": {
            "provider": provider_name,
            "dataset_path": str(dataset_path),
            "adversarial_dataset_path": str(adversarial_dataset_path) if adversarial_dataset_path else "",
            "include_adversarial": include_adversarial,
            "include_ablation": include_ablation,
            "use_llm_judge": use_llm_judge,
            "top_k": effective_config.top_k,
            "vector_weight": effective_config.vector_weight,
            "text_weight": effective_config.text_weight,
        },
        "datasets": {
            "primary": str(dataset_path),
            "adversarial": str(adversarial_dataset_path) if adversarial_dataset_path else "",
        },
        "aggregate_metrics": {
            "retrieval": retrieval_report["aggregate_metrics"],
            "answer": answer_report["aggregate_metrics"]["answer"],
            "citation": answer_report["aggregate_metrics"]["citation"],
            "abstention": answer_report["aggregate_metrics"]["abstention"],
            "adversarial": adversarial_metrics,
            "ablation": ablation_report["aggregate_metrics"] if ablation_report else {},
        },
        "per_question_results": answer_rows,
        "worst_cases": build_worst_cases(answer_rows),
        "recommendations": recommendations,
        "latency": answer_report["latency"],
        "cost_estimate": answer_report["cost_estimate"],
    }

    if not write_reports:
        return payload

    json_path, md_path = write_report_bundle(
        report_prefix="rag_full_eval",
        output_dir=output_dir,
        payload=payload,
        markdown="",
    )
    markdown = "# RAG Evaluation Report\n\n## Summary\n"
    for key, value in summary.items():
        markdown += f"- {key}: {value}\n"
    markdown += "\n## Worst Cases\n"
    markdown += "| question_id | question | expected_behavior | actual_behavior | issue | retrieved_sources |\n"
    markdown += "| --- | --- | --- | --- | --- | --- |\n"
    for row in payload["worst_cases"]:
        markdown += (
            f"| {row['question_id']} | {row['question'].replace('|', '/')} | {row['expected_behavior']} | "
            f"{row['actual_behavior']} | {row['issue'].replace('|', '/')} | {', '.join(row['retrieved_sources'])} |\n"
        )
    markdown += "\n## Correct Examples\n"
    for row in select_examples(answer_rows, correct=True):
        markdown += f"- `{row['question_id']}` {row['question']}\n"
    markdown += "\n## Problematic Examples\n"
    for row in select_examples(answer_rows, correct=False):
        markdown += f"- `{row['question_id']}` {row['question']}: {row['issue']}\n"
    markdown += "\n## Recommendations\n"
    for item in recommendations:
        markdown += f"- {item}\n"
    md_path.write_text(markdown, encoding="utf-8")
    payload["report_paths"] = {"json": str(json_path), "markdown": str(md_path)}
    return payload
