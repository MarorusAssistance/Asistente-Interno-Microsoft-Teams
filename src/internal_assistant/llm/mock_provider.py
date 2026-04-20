from __future__ import annotations

from hashlib import sha256

from internal_assistant.config import get_settings
from internal_assistant.llm.base import LLMProvider
from internal_assistant.schemas.chat import AssistantDecision


class MockLLMProvider(LLMProvider):
    def __init__(self, clarification_phrase: str = "Necesito un poco mas de detalle para responder con seguridad.") -> None:
        self.settings = get_settings()
        self.clarification_phrase = clarification_phrase
        self.embedding_dimensions = 512

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            digest = sha256(text.encode("utf-8")).digest()
            base = list(digest)
            vector = [float(base[idx % len(base)]) / 255.0 for idx in range(self.embedding_dimensions)]
            vectors.append(vector)
        return vectors

    def generate_chat_response(self, *, question: str, context_chunks: list[dict], conversation_state: dict) -> AssistantDecision:
        if not context_chunks:
            return AssistantDecision(
                answer=self.clarification_phrase,
                needs_clarification=True,
                clarification_question="Puedes indicar el sistema o el proceso exacto?",
                should_offer_incident=False,
                used_chunk_ids=[],
            )

        top_chunks = context_chunks[:2]
        answer = "Resumen basado en evidencia recuperada:\n" + "\n".join(
            f"- {chunk['content'][:220]}" for chunk in top_chunks
        )
        return AssistantDecision(
            answer=answer,
            needs_clarification=False,
            clarification_question=None,
            should_offer_incident=False,
            used_chunk_ids=[chunk["chunk_id"] for chunk in top_chunks],
        )
