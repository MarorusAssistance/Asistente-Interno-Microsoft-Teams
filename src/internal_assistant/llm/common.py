from __future__ import annotations

import json

from internal_assistant.llm.prompts import PLANNER_PROMPT, SYSTEM_PROMPT
from internal_assistant.schemas.chat import AssistantDecision, ChatPlan


def build_chat_messages(
    *,
    question: str,
    context_chunks: list[dict],
    conversation_state: dict,
) -> list[dict[str, str]]:
    context = "\n\n".join(
        f"[chunk_id={item['chunk_id']}] {item['content']}" for item in context_chunks
    )
    evidence_policy = conversation_state.get("_evidence_policy") or {}
    conversation_memory = conversation_state.get("_conversation_memory") or []
    datasource_status = conversation_state.get("_datasource_status") or {}
    planner_output = conversation_state.get("_planner_output") or {}
    memory_context = "\n\n".join(
        (
            f"[memory_id={item.get('memory_id')}, message_id={item.get('message_id')}, "
            f"role={item.get('role')}, score={item.get('score', 0):.4f}] "
            f"{item.get('memory_text', '')}"
        )
        for item in conversation_memory
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Devuelve un JSON con: answer, needs_clarification, clarification_question, "
                "should_offer_incident, used_chunk_ids.\n"
                f"Estado conversacional: {json.dumps(conversation_state, ensure_ascii=False)}\n"
                f"Politica de evidencia del turno: {json.dumps(evidence_policy, ensure_ascii=False)}\n"
                f"Plan del turno: {json.dumps(planner_output, ensure_ascii=False)}\n"
                f"Estado de datasources consultados: {json.dumps(datasource_status, ensure_ascii=False)}\n"
                "Si la politica indica requires_direct_evidence=true, no conviertas casos similares en solucion cerrada.\n"
                "Si no puedes justificar la respuesta con evidencia directa, devuelve needs_clarification=true.\n"
                "Si el turno es un follow-up insatisfecho y hay memoria conversacional recuperada, "
                "usa esa memoria para entender a que respuesta anterior se refiere el usuario.\n"
                "Si ademas hay documentos directos en el indice de conocimiento, responde con una version mas concreta; "
                "no pidas aclaracion solo porque el mensaje actual no repita todos los detalles.\n"
                f"Memoria conversacional recuperada:\n{memory_context or '[sin memoria consultada o sin resultados]'}\n"
                f"Pregunta: {question}\n"
                f"Contexto del indice de conocimiento:\n{context or '[indice no consultado o sin resultados]'}"
            ),
        },
    ]


def build_planner_messages(*, message: str, recent_messages: list[dict], conversation_state: dict) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": PLANNER_PROMPT},
        {
            "role": "user",
            "content": (
                f"Mensaje actual: {message}\n"
                f"Estado conversacional: {json.dumps(conversation_state, ensure_ascii=False)}\n"
                f"Mensajes recientes: {json.dumps(recent_messages, ensure_ascii=False)}"
            ),
        },
    ]


def parse_chat_plan(content: str | None, *, fallback_message: str) -> ChatPlan:
    raw = (content or "").strip()
    if not raw:
        raise ValueError("El proveedor LLM devolvio un plan vacio")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("El proveedor LLM devolvio JSON de plan malformado") from None
        payload = json.loads(raw[start : end + 1])

    plan = ChatPlan.model_validate(payload)
    if plan.needs_knowledge_index and not plan.knowledge_index_query.strip():
        plan.knowledge_index_query = fallback_message
    if plan.needs_conversation_memory and not plan.conversation_memory_query.strip():
        plan.conversation_memory_query = fallback_message
    return plan


def parse_assistant_decision(content: str | None) -> AssistantDecision:
    raw = (content or "").strip()
    if not raw:
        raise ValueError("El proveedor LLM devolvio una respuesta vacia")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("El proveedor LLM devolvio JSON malformado") from None
        payload = json.loads(raw[start : end + 1])

    return AssistantDecision.model_validate(payload)


def validate_embedding_dimensions(embeddings: list[list[float]], expected_dimensions: int) -> list[list[float]]:
    for index, embedding in enumerate(embeddings):
        if len(embedding) != expected_dimensions:
            raise ValueError(
                f"Embedding con dimension invalida en posicion {index}: "
                f"se esperaba {expected_dimensions} y se obtuvo {len(embedding)}"
            )
    return embeddings
