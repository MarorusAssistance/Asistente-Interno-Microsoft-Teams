from __future__ import annotations

import time
from typing import Any

import httpx
from sqlalchemy.orm import Session

from internal_assistant.cards import build_feedback_card, build_incident_confirmation_card, build_sources_card
from internal_assistant.chat.incident_draft import build_confirmation_text, extract_incident_fields, missing_fields, validate_draft
from internal_assistant.chat.intents import detect_intent
from internal_assistant.config import get_settings
from internal_assistant.llm import LLMProvider, build_default_provider
from internal_assistant.observability import get_logger
from internal_assistant.repositories import ConversationRepository, FeedbackRepository, IncidentRepository, MessageRepository, RetrievalLogRepository
from internal_assistant.rag import HybridRetriever
from internal_assistant.schemas import ChatRequest, ChatResponse, FeedbackCreate, SourceSnippet

logger = get_logger(__name__)


class ChatService:
    def __init__(self, session: Session, llm_provider: LLMProvider | None = None) -> None:
        self.session = session
        self.settings = get_settings()
        self.llm_provider = llm_provider or build_default_provider()
        self.conversations = ConversationRepository(session)
        self.messages = MessageRepository(session)
        self.incidents = IncidentRepository(session)
        self.feedback = FeedbackRepository(session)
        self.retrieval_logs = RetrievalLogRepository(session)
        self.retriever = HybridRetriever(session)

    def handle_chat(self, request: ChatRequest) -> ChatResponse:
        started_at = time.perf_counter()
        conversation = self.conversations.get_or_create(
            request.conversation_id,
            user_id=request.user_id,
            channel_id=request.channel,
            teams_conversation_id=request.teams_conversation_id,
        )
        state = dict(conversation.state or {})
        intent = detect_intent(request.message, state)
        user_message = self.messages.create(conversation.id, "user", request.message, intent=intent)

        if intent == "feedback":
            return self._handle_feedback_message(conversation.id, user_message.id, request)

        if intent in {"register_incident", "confirm_incident"} or state.get("pending_incident_draft"):
            response = self._handle_incident_flow(conversation.id, state, request)
            self.conversations.save_state(conversation, response.pop("_state"))
            assistant_message = self.messages.create(
                conversation.id,
                "assistant",
                response["answer"],
                intent="register_incident",
                created_ticket_id=response.get("created_ticket_id"),
            )
            self.session.commit()
            response["message_id"] = assistant_message.id
            return ChatResponse(**response)

        response = self._handle_qa_flow(conversation.id, state, request, intent, user_message.id, started_at)
        self.conversations.save_state(conversation, response.pop("_state"))
        assistant_message = self.messages.create(conversation.id, "assistant", response["answer"], intent=intent)
        self.session.commit()
        response["message_id"] = assistant_message.id
        return ChatResponse(**response)

    def save_feedback(self, payload: FeedbackCreate) -> None:
        self.feedback.create(payload)
        self.session.commit()

    def _handle_feedback_message(self, conversation_id: int, message_id: int, request: ChatRequest) -> ChatResponse:
        feedback_type = "useful" if request.message.strip().lower().startswith(("util", "útil")) else "not_useful"
        payload = FeedbackCreate(
            conversation_id=conversation_id,
            message_id=message_id,
            user_id=request.user_id,
            feedback_type=feedback_type,
            comment=request.message,
        )
        self.feedback.create(payload)
        self.session.commit()
        answer = "Gracias. He registrado tu feedback para mejorar futuras respuestas."
        return ChatResponse(
            conversation_id=conversation_id,
            answer=answer,
            sources=[],
            related_incidents=[],
            needs_clarification=False,
            clarification_attempt=0,
            should_offer_incident=False,
            adaptive_card=build_feedback_card(),
            fallback_text=answer,
        )

    def _handle_incident_flow(self, conversation_id: int, state: dict, request: ChatRequest) -> dict[str, Any]:
        draft = dict(state.get("pending_incident_draft") or {})
        if state.get("offer_incident") and not draft:
            draft["is_resolved"] = False
            state["offer_incident"] = False
        if draft.get("awaiting_confirmation") and request.message.strip().lower() in {"si", "sí", "confirmo", "confirmar"}:
            payload = validate_draft({key: value for key, value in draft.items() if key != "awaiting_confirmation"})
            created = self._create_incident(payload.model_dump())
            self._trigger_index_incident(created["id"])
            new_state = {"clarification_attempts": 0}
            answer = f"Incidencia creada e indexada correctamente: {created['external_id']}."
            return {
                "conversation_id": conversation_id,
                "answer": answer,
                "sources": [],
                "related_incidents": [],
                "needs_clarification": False,
                "clarification_attempt": 0,
                "should_offer_incident": False,
                "adaptive_card": build_incident_confirmation_card(created),
                "fallback_text": answer,
                "created_ticket_id": created["id"],
                "created_ticket_external_id": created["external_id"],
                "_state": new_state,
            }

        draft.update(extract_incident_fields(request.message))
        state["pending_incident_draft"] = draft
        missing = missing_fields(draft)
        if missing:
            next_field = missing[0]
            prompts = {
                "title": "Necesito el titulo de la incidencia. Usa por ejemplo: titulo: Acceso fallido en SafeGate",
                "description": "Necesito la descripcion del problema. Usa: descripcion: ...",
                "department": "Necesito el departamento. Opciones sugeridas: Operaciones, Seguridad, Onboarding, Politicas internas.",
                "category": "Necesito la categoria. Usa: categoria: ...",
                "affected_system": "Necesito el sistema afectado. Ejemplos: LogiCore ERP, RutaNexo, AlmaTrack WMS, SafeGate, OnboardHub, DocuFlow.",
                "is_resolved": "Indica si ya esta resuelta. Puedes escribir: resuelta: si o resuelta: no",
                "impact": "Para incidencias no resueltas necesito el impacto. Usa: impacto: ...",
                "expected_behavior": "Describe el comportamiento esperado. Usa: esperado: ...",
                "actual_behavior": "Describe el comportamiento actual. Usa: actual: ...",
            }
            answer = prompts.get(next_field, f"Necesito el campo {next_field}.")
            return {
                "conversation_id": conversation_id,
                "answer": answer,
                "sources": [],
                "related_incidents": [],
                "needs_clarification": False,
                "clarification_attempt": state.get("clarification_attempts", 0),
                "should_offer_incident": False,
                "adaptive_card": None,
                "fallback_text": answer,
                "_state": state,
            }

        draft["awaiting_confirmation"] = True
        state["pending_incident_draft"] = draft
        answer = build_confirmation_text(draft)
        return {
            "conversation_id": conversation_id,
            "answer": answer,
            "sources": [],
            "related_incidents": [],
            "needs_clarification": False,
            "clarification_attempt": state.get("clarification_attempts", 0),
            "should_offer_incident": False,
            "adaptive_card": None,
            "fallback_text": answer,
            "_state": state,
        }

    def _handle_qa_flow(
        self,
        conversation_id: int,
        state: dict,
        request: ChatRequest,
        intent: str,
        user_message_id: int,
        started_at: float,
    ) -> dict[str, Any]:
        clarification_attempts = int(state.get("clarification_attempts", 0))
        query_embedding = self.llm_provider.embed_texts([request.message])[0]
        retrieved = self.retriever.search(request.message, query_embedding, limit=5)
        confidence = retrieved[0].final_score if retrieved else 0.0

        if not retrieved or confidence < self.settings.retrieval_confidence_threshold:
            clarification_attempts += 1
            state["clarification_attempts"] = clarification_attempts
            if clarification_attempts >= 3:
                state["offer_incident"] = True
                answer = (
                    "No tengo evidencia suficiente en el indice para responder con seguridad. "
                    "Si quieres, puedo ayudarte a registrar una incidencia no resuelta."
                )
                self._write_retrieval_log(
                    conversation_id=conversation_id,
                    message_id=user_message_id,
                    query=request.message,
                    intent=intent,
                    answer=answer,
                    confidence=confidence,
                    latency_ms=int((time.perf_counter() - started_at) * 1000),
                )
                return {
                    "conversation_id": conversation_id,
                    "answer": answer,
                    "sources": [],
                    "related_incidents": [],
                    "needs_clarification": False,
                    "clarification_attempt": clarification_attempts,
                    "should_offer_incident": True,
                    "adaptive_card": None,
                    "fallback_text": answer,
                    "_state": state,
                }

            full_answer = (
                "Necesito un poco mas de detalle para responder con seguridad. "
                f"Puedes concretar el sistema, el proceso o el error exacto? Intento de aclaracion {clarification_attempts} de 2."
            )
            self._write_retrieval_log(
                conversation_id=conversation_id,
                message_id=user_message_id,
                query=request.message,
                intent=intent,
                answer=full_answer,
                confidence=confidence,
                latency_ms=int((time.perf_counter() - started_at) * 1000),
            )
            return {
                "conversation_id": conversation_id,
                "answer": full_answer,
                "sources": [],
                "related_incidents": [],
                "needs_clarification": True,
                "clarification_attempt": clarification_attempts,
                "should_offer_incident": False,
                "adaptive_card": None,
                "fallback_text": full_answer,
                "_state": state,
            }

        sources = [
            SourceSnippet(
                source_type=item.source_type,
                source_id=item.source_id,
                title=item.metadata.get("title", f"{item.source_type}-{item.source_id}"),
                source_url=item.metadata.get("source_url"),
                excerpt=item.content[:260],
                chunk_id=item.chunk_id,
            )
            for item in retrieved
        ]
        context_chunks = [
            {
                "chunk_id": item.chunk_id,
                "content": item.content,
                "source_type": item.source_type,
                "source_id": item.source_id,
                "metadata": item.metadata,
            }
            for item in retrieved
        ]
        decision = self.llm_provider.generate_chat_response(
            question=request.message,
            context_chunks=context_chunks,
            conversation_state=state,
        )
        state["clarification_attempts"] = 0
        state["offer_incident"] = False
        related_incidents = [
            {
                "id": incident.id,
                "external_id": incident.external_id,
                "title": incident.title,
                "status": incident.status,
            }
            for incident in self.incidents.list_related(
                list({item.source_id for item in retrieved if item.source_type == "incident"})
            )
        ]
        answer = decision.answer
        self.retrieval_logs.create(
            conversation_id=conversation_id,
            message_id=user_message_id,
            query=request.message,
            detected_intent=intent,
            retrieved_chunk_ids=[item.chunk_id for item in retrieved],
            retrieved_source_ids=[item.source_id for item in retrieved],
            scores={item.chunk_id: item.final_score for item in retrieved},
            confidence_score=confidence,
            was_answered=not decision.needs_clarification,
            tokens_input_estimated=len(request.message.split()) + sum(len(item.content.split()) for item in retrieved),
            tokens_output_estimated=len(answer.split()),
            latency_ms=int((time.perf_counter() - started_at) * 1000),
            answer=answer,
        )
        return {
            "conversation_id": conversation_id,
            "answer": answer,
            "sources": [source.model_dump() for source in sources],
            "related_incidents": related_incidents,
            "needs_clarification": decision.needs_clarification,
            "clarification_attempt": 0,
            "should_offer_incident": decision.should_offer_incident,
            "adaptive_card": build_sources_card(answer, [source.model_dump() for source in sources], related_incidents),
            "fallback_text": self._build_sources_fallback(answer, sources),
            "_state": state,
        }

    def _build_sources_fallback(self, answer: str, sources: list[SourceSnippet]) -> str:
        lines = [answer, "", "Fuentes:"]
        for source in sources:
            suffix = source.source_url or source.excerpt
            lines.append(f"- {source.title}: {suffix}")
        return "\n".join(lines)

    def _write_retrieval_log(self, *, conversation_id: int, message_id: int, query: str, intent: str, answer: str, confidence: float, latency_ms: int) -> None:
        self.retrieval_logs.create(
            conversation_id=conversation_id,
            message_id=message_id,
            query=query,
            detected_intent=intent,
            retrieved_chunk_ids=[],
            retrieved_source_ids=[],
            scores={},
            confidence_score=confidence,
            was_answered=False,
            tokens_input_estimated=len(query.split()),
            tokens_output_estimated=len(answer.split()),
            latency_ms=latency_ms,
            answer=answer,
        )

    def _create_incident(self, payload: dict) -> dict:
        headers = {"x-app-shared-secret": self.settings.app_shared_secret}
        with httpx.Client(timeout=30) as client:
            response = client.post(f"{self.settings.custom_incidents_api_base_url}/incidents", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    def _trigger_index_incident(self, incident_id: int) -> None:
        headers = {"x-app-shared-secret": self.settings.app_shared_secret}
        with httpx.Client(timeout=30) as client:
            response = client.post(f"{self.settings.indexer_api_base_url}/index/incident/{incident_id}", headers=headers)
            response.raise_for_status()
