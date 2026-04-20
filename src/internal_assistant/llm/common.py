from __future__ import annotations

import json

from internal_assistant.llm.prompts import SYSTEM_PROMPT
from internal_assistant.schemas.chat import AssistantDecision


def build_chat_messages(*, question: str, context_chunks: list[dict], conversation_state: dict) -> list[dict[str, str]]:
    context = "\n\n".join(
        f"[chunk_id={item['chunk_id']}] {item['content']}" for item in context_chunks
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Devuelve un JSON con: answer, needs_clarification, clarification_question, "
                "should_offer_incident, used_chunk_ids.\n"
                f"Estado conversacional: {json.dumps(conversation_state, ensure_ascii=False)}\n"
                f"Pregunta: {question}\n"
                f"Contexto:\n{context}"
            ),
        },
    ]


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
