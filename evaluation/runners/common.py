from __future__ import annotations

from dataclasses import asdict
from typing import Any

from internal_assistant.rag import RetrievalConfig


ABLATION_CONFIGS = [
    ("vector_only", RetrievalConfig(top_k=5, vector_weight=1.0, text_weight=0.0)),
    ("text_only", RetrievalConfig(top_k=5, vector_weight=0.0, text_weight=1.0)),
    ("hybrid_default", RetrievalConfig(top_k=5, vector_weight=0.70, text_weight=0.30)),
    ("hybrid_text_heavier", RetrievalConfig(top_k=5, vector_weight=0.50, text_weight=0.50)),
    ("hybrid_vector_heavier", RetrievalConfig(top_k=5, vector_weight=0.85, text_weight=0.15)),
    ("hybrid_top_8", RetrievalConfig(top_k=8, vector_weight=0.70, text_weight=0.30)),
]


def retrieval_config_to_dict(config: RetrievalConfig) -> dict[str, Any]:
    return asdict(config.normalized())


def issue_for_row(row: dict[str, Any]) -> str:
    if row.get("actual_behavior") and row.get("expected_behavior") and row.get("actual_behavior") != row.get("expected_behavior"):
        return f"Comportamiento esperado {row['expected_behavior']} pero obtuvo {row['actual_behavior']}"
    if row.get("expected_source_ids") and not set(row.get("expected_source_ids", [])).intersection(row.get("retrieved_source_ids", [])):
        return "No recupero ninguna fuente esperada"
    if row.get("expected_behavior") == "answer_with_sources" and not row.get("citation_present"):
        return "La respuesta no incluyo fuentes"
    if row.get("unsupported_answer"):
        return "Respondio sin evidencia suficiente"
    failed = row.get("failed_checks", 0)
    if failed:
        return f"Fallo {failed} comprobaciones heuristicas"
    return "Caso con bajo rendimiento relativo"


def failed_check_count(row: dict[str, Any]) -> int:
    bool_keys = [
        "answer_generated",
        "answer_contains_required_terms",
        "answer_avoids_forbidden_terms",
        "answer_mentions_uncertainty_when_needed",
        "answer_uses_only_retrieved_context",
        "answer_expected_behavior_match",
        "citation_present",
        "citation_source_validity",
        "citation_coverage",
    ]
    return sum(1 for key in bool_keys if key in row and row.get(key) is False)


def build_worst_cases(rows: list[dict[str, Any]], *, limit: int = 10) -> list[dict[str, Any]]:
    ranked = []
    for row in rows:
        enriched = dict(row)
        enriched["failed_checks"] = failed_check_count(enriched)
        enriched.setdefault("issue", issue_for_row(enriched))
        ranked.append(enriched)
    ranked.sort(
        key=lambda item: (
            int(item.get("failed_checks", 0)),
            1 if item.get("actual_behavior") != item.get("expected_behavior") else 0,
            float(item.get("latency_ms", 0.0)),
        ),
        reverse=True,
    )
    return [
        {
            "question_id": item.get("turn_id", item.get("question_id", "")),
            "question": item.get("question", ""),
            "expected_behavior": item.get("expected_behavior", ""),
            "actual_behavior": item.get("actual_behavior", ""),
            "issue": item.get("issue", ""),
            "retrieved_sources": list(item.get("retrieved_source_ids", [])),
        }
        for item in ranked[:limit]
    ]


def select_examples(rows: list[dict[str, Any]], *, correct: bool, limit: int = 5) -> list[dict[str, Any]]:
    filtered = []
    for row in rows:
        is_correct = bool(row.get("is_correct")) if "is_correct" in row else bool(row.get("hit_at_5"))
        if is_correct is correct:
            filtered.append(row)
    filtered.sort(key=lambda item: float(item.get("latency_ms", 0.0)))
    return [
        {
            "question_id": item.get("turn_id", item.get("question_id", "")),
            "question": item.get("question", ""),
            "issue": item.get("issue", issue_for_row(item)),
        }
        for item in filtered[:limit]
    ]


def retrieval_recommendations(metrics: dict[str, Any]) -> list[str]:
    recommendations: list[str] = []
    if float(metrics.get("hit_at_5", 0.0)) < 0.70:
        recommendations.append("Revisar chunking y pesos del retrieval hibrido; el hit@5 sigue siendo bajo.")
    if float(metrics.get("source_type_match_rate", 0.0)) < 0.70:
        recommendations.append("Ajustar consultas o metadata para recuperar mejor el tipo de fuente esperado.")
    if float(metrics.get("average_latency_ms", 0.0)) > 1500:
        recommendations.append("Reducir top_k o candidatos intermedios para bajar latencia media.")
    if not recommendations:
        recommendations.append("La configuracion actual de retrieval es razonable para seguir afinando la calidad de respuesta.")
    return recommendations


def answer_recommendations(
    answer_metrics: dict[str, Any],
    citation_metrics: dict[str, Any],
    abstention_metrics: dict[str, Any],
) -> list[str]:
    recommendations: list[str] = []
    if float(answer_metrics.get("answer_expected_behavior_match", 0.0)) < 0.70:
        recommendations.append("Revisar la logica de clasificacion y el prompt para alinear mejor el comportamiento esperado.")
    if float(citation_metrics.get("citation_coverage_rate", 0.0)) < 0.70:
        recommendations.append("Mejorar la seleccion de fuentes y la obligacion de citarlas en la respuesta final.")
    if float(abstention_metrics.get("false_answer_when_should_abstain", 0.0)) > 0.20:
        recommendations.append("Subir el umbral de confianza o endurecer la abstencion cuando no haya evidencia suficiente.")
    if float(abstention_metrics.get("clarification_rate_when_required", 0.0)) < 0.70:
        recommendations.append("Forzar con mas claridad el camino de aclaracion en preguntas ambiguas.")
    if not recommendations:
        recommendations.append("La calidad heuristica es consistente; el siguiente paso util es comparar configuraciones de retrieval.")
    return recommendations
