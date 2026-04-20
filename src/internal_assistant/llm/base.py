from __future__ import annotations

from abc import ABC, abstractmethod

from internal_assistant.schemas.chat import AssistantDecision


class LLMProvider(ABC):
    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    @abstractmethod
    def generate_chat_response(self, *, question: str, context_chunks: list[dict], conversation_state: dict) -> AssistantDecision:
        raise NotImplementedError
