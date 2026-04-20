from __future__ import annotations

import json

from openai import OpenAI

from internal_assistant.config import get_settings
from internal_assistant.llm.base import LLMProvider
from internal_assistant.llm.mock_provider import MockLLMProvider
from internal_assistant.llm.prompts import SYSTEM_PROMPT
from internal_assistant.schemas.chat import AssistantDecision


class OpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.client = OpenAI(api_key=settings.openai_api_key)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(
            model=self.settings.embedding_model,
            input=texts,
            dimensions=self.settings.embedding_dimensions,
        )
        return [item.embedding for item in response.data]

    def generate_chat_response(self, *, question: str, context_chunks: list[dict], conversation_state: dict) -> AssistantDecision:
        context = "\n\n".join(
            f"[chunk_id={item['chunk_id']}] {item['content']}" for item in context_chunks
        )
        response = self.client.chat.completions.create(
            model=self.settings.chat_model,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
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
            ],
        )
        payload = json.loads(response.choices[0].message.content)
        return AssistantDecision.model_validate(payload)


def build_default_provider() -> LLMProvider:
    settings = get_settings()
    if settings.openai_api_key:
        return OpenAIProvider()
    return MockLLMProvider()
