from __future__ import annotations

from openai import OpenAI

from internal_assistant.config import get_settings
from internal_assistant.llm.base import LLMProvider
from internal_assistant.llm.common import build_chat_messages, parse_assistant_decision, validate_embedding_dimensions
from internal_assistant.llm.mock_provider import MockLLMProvider
from internal_assistant.llm.openai_compatible_provider import OpenAICompatibleProvider
from internal_assistant.schemas.chat import AssistantDecision


EMBEDDING_BATCH_SIZE = 32


class OpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.client = OpenAI(api_key=settings.openai_api_key, max_retries=0, timeout=120.0)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for start in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            batch = texts[start : start + EMBEDDING_BATCH_SIZE]
            response = self.client.embeddings.create(
                model=self.settings.embedding_model,
                input=batch,
                dimensions=self.settings.embedding_dimensions,
            )
            embeddings.extend(item.embedding for item in response.data)
        return validate_embedding_dimensions(embeddings, self.settings.embedding_dimensions)

    def generate_chat_response(self, *, question: str, context_chunks: list[dict], conversation_state: dict) -> AssistantDecision:
        response = self.client.chat.completions.create(
            model=self.settings.chat_model,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=build_chat_messages(
                question=question,
                context_chunks=context_chunks,
                conversation_state=conversation_state,
            ),
        )
        return parse_assistant_decision(response.choices[0].message.content)


def _is_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in {"", "<your-openai-api-key>", "your-openai-api-key", "change-me", "set-me"}


def normalize_provider_name(value: str) -> str:
    normalized = value.strip().lower()
    aliases = {
        "openai-compatible": "openai_compatible",
        "local": "openai_compatible",
    }
    return aliases.get(normalized, normalized)


def resolve_provider_name(settings=None) -> str:
    current_settings = settings or get_settings()
    provider = normalize_provider_name(current_settings.llm_provider or "auto")
    if provider in {"", "auto"}:
        if current_settings.llm_base_url:
            return "openai_compatible"
        if not _is_placeholder(current_settings.openai_api_key):
            return "openai"
        return "mock"
    return provider


def build_default_provider() -> LLMProvider:
    settings = get_settings()
    provider = resolve_provider_name(settings)
    if provider == "mock":
        return MockLLMProvider()
    if provider == "openai":
        return OpenAIProvider()
    if provider == "openai_compatible":
        return OpenAICompatibleProvider()
    raise ValueError(f"LLM_PROVIDER no soportado: {settings.llm_provider}")
