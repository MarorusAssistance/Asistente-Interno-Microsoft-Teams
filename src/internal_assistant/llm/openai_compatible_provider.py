from __future__ import annotations

from openai import OpenAI

from internal_assistant.config import get_settings
from internal_assistant.llm.base import LLMProvider
from internal_assistant.llm.common import (
    build_chat_messages,
    build_planner_messages,
    parse_assistant_decision,
    parse_chat_plan,
    validate_embedding_dimensions,
)
from internal_assistant.observability.tracing import set_span_attributes, start_span
from internal_assistant.schemas.chat import AssistantDecision, ChatPlan


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
            timeout=settings.llm_timeout_seconds,
        )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        with start_span(
            "llm.embeddings",
            {
                "llm.provider": "openai_compatible",
                "llm.embedding_model": self.settings.embedding_model,
                "llm.embedding_dimensions": self.settings.embedding_dimensions,
                "llm.embedding_input_count": len(texts),
            },
        ) as span:
            embeddings: list[list[float]] = []
            for start in range(0, len(texts), EMBEDDING_BATCH_SIZE):
                batch = texts[start : start + EMBEDDING_BATCH_SIZE]
                response = self.client.embeddings.create(
                    model=self.settings.embedding_model,
                    input=batch,
                )
                embeddings.extend(item.embedding for item in response.data)
            validated = validate_embedding_dimensions(embeddings, self.settings.embedding_dimensions)
            set_span_attributes(span, {"llm.embedding_output_count": len(validated)})
            return validated

    def generate_chat_response(self, *, question: str, context_chunks: list[dict], conversation_state: dict) -> AssistantDecision:
        with start_span(
            "llm.chat_completion",
            {
                "llm.provider": "openai_compatible",
                "llm.chat_model": self.settings.chat_model,
                "llm.context_chunk_count": len(context_chunks),
                "question.length": len(question),
                "llm.timeout_seconds": self.settings.llm_timeout_seconds,
            },
        ) as span:
            response = self.client.chat.completions.create(
                model=self.settings.chat_model,
                temperature=0.1,
                messages=build_chat_messages(
                    question=question,
                    context_chunks=context_chunks,
                    conversation_state=conversation_state,
                ),
            )
            decision = parse_assistant_decision(response.choices[0].message.content)
            set_span_attributes(
                span,
                {
                    "llm.needs_clarification": decision.needs_clarification,
                    "llm.should_offer_incident": decision.should_offer_incident,
                    "llm.used_chunk_ids": decision.used_chunk_ids,
                    "llm.answer_length": len(decision.answer or ""),
                },
            )
            return decision

    def plan_chat(self, *, message: str, recent_messages: list[dict], conversation_state: dict) -> ChatPlan:
        with start_span(
            "llm.chat_planner",
            {
                "llm.provider": "openai_compatible",
                "llm.chat_model": self.settings.chat_model,
                "planner.recent_message_count": len(recent_messages),
                "message.length": len(message),
                "llm.timeout_seconds": self.settings.llm_timeout_seconds,
            },
        ) as span:
            response = self.client.chat.completions.create(
                model=self.settings.chat_model,
                temperature=0.0,
                messages=build_planner_messages(
                    message=message,
                    recent_messages=recent_messages,
                    conversation_state=conversation_state,
                ),
            )
            plan = parse_chat_plan(response.choices[0].message.content, fallback_message=message)
            set_span_attributes(
                span,
                {
                    "planner.needs_conversation_memory": plan.needs_conversation_memory,
                    "planner.needs_knowledge_index": plan.needs_knowledge_index,
                    "planner.can_answer_from_conversation_only": plan.can_answer_from_conversation_only,
                    "planner.should_ask_clarification_first": plan.should_ask_clarification_first,
                },
            )
            return plan
