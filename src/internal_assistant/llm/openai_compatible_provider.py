from __future__ import annotations

from openai import OpenAI

from internal_assistant.config import get_settings
from internal_assistant.llm.base import LLMProvider
from internal_assistant.llm.common import build_chat_messages, parse_assistant_decision, validate_embedding_dimensions
from internal_assistant.schemas.chat import AssistantDecision


EMBEDDING_BATCH_SIZE = 32


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.llm_base_url:
            raise ValueError("LLM_BASE_URL es obligatorio cuando LLM_PROVIDER=openai_compatible")

        self.settings = settings
        self.client = OpenAI(
            api_key=settings.llm_api_key or "local-dev-key",
            base_url=settings.llm_base_url,
            max_retries=0,
            timeout=120.0,
        )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for start in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            batch = texts[start : start + EMBEDDING_BATCH_SIZE]
            response = self.client.embeddings.create(
                model=self.settings.embedding_model,
                input=batch,
            )
            embeddings.extend(item.embedding for item in response.data)
        return validate_embedding_dimensions(embeddings, self.settings.embedding_dimensions)

    def generate_chat_response(self, *, question: str, context_chunks: list[dict], conversation_state: dict) -> AssistantDecision:
        response = self.client.chat.completions.create(
            model=self.settings.chat_model,
            temperature=0.1,
            messages=build_chat_messages(
                question=question,
                context_chunks=context_chunks,
                conversation_state=conversation_state,
            ),
        )
        return parse_assistant_decision(response.choices[0].message.content)
