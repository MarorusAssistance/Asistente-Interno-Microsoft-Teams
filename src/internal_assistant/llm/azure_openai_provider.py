from __future__ import annotations

from internal_assistant.llm.base import LLMProvider
from internal_assistant.schemas.chat import AssistantDecision


class AzureOpenAIProvider(LLMProvider):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("AzureOpenAIProvider queda preparado para una segunda fase")

    def generate_chat_response(self, *, question: str, context_chunks: list[dict], conversation_state: dict) -> AssistantDecision:
        raise NotImplementedError("AzureOpenAIProvider queda preparado para una segunda fase")
