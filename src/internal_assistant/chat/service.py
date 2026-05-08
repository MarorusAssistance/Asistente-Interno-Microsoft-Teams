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
from internal_assistant.llm.common import build_chat_messages
from internal_assistant.observability import RagTrace, get_logger, start_span
from internal_assistant.observability.tracing import (
    retrieval_span_attributes,
    serialize_chunks_for_langsmith,
    serialize_context_for_langsmith,
    serialize_decision_for_langsmith,
    set_span_attributes,
    user_hash,
)
from internal_assistant.repositories import ConversationRepository, FeedbackRepository, IncidentRepository, MessageRepository, RetrievalLogRepository
from internal_assistant.rag import DEFAULT_RETRIEVAL_CONFIG, HybridRetriever, RetrievalConfig
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

    def classify_intent(self, message: str, state: dict | None = None) -> str:
        return detect_intent(message, state)

    def retrieve(
        self,
        message: str,
        retrieval_config: RetrievalConfig | None = None,
    ) -> list:
        query_embedding = self.llm_provider.embed_texts([message])[0]
        return self.retriever.search(message, query_embedding, config=retrieval_config or DEFAULT_RETRIEVAL_CONFIG)

    def calculate_confidence(self, retrieved: list) -> float:
        return retrieved[0].final_score if retrieved else 0.0

    def generate_answer(self, question: str, retrieved_chunks: list, conversation_state: dict) -> tuple[Any, list[dict[str, Any]]]:
        context_chunks = [
            {
                "chunk_id": item.chunk_id,
                "content": item.content,
                "source_type": item.source_type,
                "source_id": item.source_id,
                "metadata": item.metadata,
            }
            for item in retrieved_chunks
        ]
        decision = self.llm_provider.generate_chat_response(
            question=question,
            context_chunks=context_chunks,
            conversation_state=conversation_state,
        )
        return decision, context_chunks

    def simulate_chat(
        self,
        request: ChatRequest,
        *,
        state: dict | None = None,
        retrieval_config: RetrievalConfig | None = None,
    ) -> tuple[ChatResponse, dict[str, Any], dict[str, Any]]:
        current_state = dict(state or {})
        intent = self.classify_intent(request.message, current_state)
        if current_state.get("pending_incident_draft"):
            raise ValueError("El flujo de evaluacion solo soporta preguntas/respuestas del asistente RAG")
        if intent in {"feedback", "register_incident", "confirm_incident"}:
            intent = "question_answer"

        trace = RagTrace.from_settings(self.settings)
        with trace.start_run(
            "rag.chat",
            inputs={"question": request.message, "channel": request.channel},
            metadata={
                "conversation_id": request.conversation_id or 0,
                "user_id_hash": user_hash(request.user_id),
                "mode": "simulation",
            },
        ) as trace_run:
            response = self._handle_qa_flow(
                conversation_id=request.conversation_id or 0,
                state=current_state,
                request=request,
                intent=intent,
                user_message_id=0,
                started_at=time.perf_counter(),
                write_retrieval_logs=False,
                retrieval_config=retrieval_config,
                trace_run=trace_run,
            )
            meta = response.pop("_meta", {})
            next_state = response.pop("_state")
            chat_response = ChatResponse(**response)
            trace_run.set_outputs(self._trace_response_payload(chat_response))
            return chat_response, next_state, meta

    def handle_chat(self, request: ChatRequest) -> ChatResponse:
        started_at = time.perf_counter()
        trace = RagTrace.from_settings(self.settings)
        with trace.start_run(
            "rag.chat",
            inputs={"question": request.message, "channel": request.channel},
            metadata={
                "conversation_id": request.conversation_id,
                "user_id_hash": user_hash(request.user_id),
                "provider": getattr(self.settings, "llm_provider", ""),
                "chat_model": getattr(self.settings, "chat_model", ""),
                "embedding_model": getattr(self.settings, "embedding_model", ""),
            },
        ) as trace_run, start_span(
            "chat.request",
            {
                "channel": request.channel,
                "conversation_id": request.conversation_id or 0,
                "user_id_hash": user_hash(request.user_id),
                "message.length": len(request.message),
                "llm.provider": getattr(self.settings, "llm_provider", ""),
                "llm.chat_model": getattr(self.settings, "chat_model", ""),
                "llm.embedding_model": getattr(self.settings, "embedding_model", ""),
            },
        ) as request_span:
            conversation = self.conversations.get_or_create(
                request.conversation_id,
                user_id=request.user_id,
                channel_id=request.channel,
                teams_conversation_id=request.teams_conversation_id,
            )
            state = dict(conversation.state or {})
            intent = self.classify_intent(request.message, state)
            set_span_attributes(
                request_span,
                {"conversation_id": conversation.id, "detected_intent": intent},
            )
            user_message = self.messages.create(conversation.id, "user", request.message, intent=intent)

            if intent == "feedback":
                chat_response = self._handle_feedback_message(conversation.id, user_message.id, request)
                trace_run.set_outputs(self._trace_response_payload(chat_response))
                set_span_attributes(
                    request_span,
                    {
                        "chat.status": "ok",
                        "message_id": chat_response.message_id or 0,
                        "answer.length": len(chat_response.answer),
                    },
                )
                return chat_response

            if intent in {"register_incident", "confirm_incident"} or state.get("pending_incident_draft"):
                with trace_run.child(
                    "rag.incident_flow",
                    run_type="chain",
                    inputs={"message": request.message, "state": state},
                ) as incident_run:
                    response = self._handle_incident_flow(conversation.id, state, request)
                    incident_run.set_outputs(
                        {
                            "answer": response.get("answer"),
                            "created_ticket_id": response.get("created_ticket_id"),
                            "created_ticket_external_id": response.get("created_ticket_external_id"),
                        }
                    )
                with start_span(
                    "chat.persist",
                    {"conversation_id": conversation.id, "intent": "register_incident"},
                ):
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
                chat_response = ChatResponse(**response)
                trace_run.set_outputs(self._trace_response_payload(chat_response))
                set_span_attributes(
                    request_span,
                    {
                        "chat.status": "ok",
                        "message_id": chat_response.message_id or 0,
                        "answer.length": len(chat_response.answer),
                    },
                )
                return chat_response

            response = self._handle_qa_flow(
                conversation.id,
                state,
                request,
                intent,
                user_message.id,
                started_at,
                trace_run=trace_run,
            )
            with start_span("chat.persist", {"conversation_id": conversation.id, "intent": intent}):
                self.conversations.save_state(conversation, response.pop("_state"))
                assistant_message = self.messages.create(conversation.id, "assistant", response["answer"], intent=intent)
                self.session.commit()
            response["message_id"] = assistant_message.id
            chat_response = ChatResponse(**response)
            trace_run.set_outputs(self._trace_response_payload(chat_response))
            set_span_attributes(
                request_span,
                {
                    "chat.status": "ok",
                    "message_id": chat_response.message_id or 0,
                    "answer.length": len(chat_response.answer),
                    "source.count": len(chat_response.sources),
                    "needs_clarification": chat_response.needs_clarification,
                    "should_offer_incident": chat_response.should_offer_incident,
                },
            )
            return chat_response

    def save_feedback(self, payload: FeedbackCreate) -> None:
        with start_span(
            "chat.persist",
            {
                "persist.feedback": True,
                "conversation_id": payload.conversation_id,
                "message_id": payload.message_id or 0,
                "feedback_type": payload.feedback_type,
            },
        ):
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
        with start_span(
            "chat.persist",
            {
                "persist.feedback": True,
                "conversation_id": conversation_id,
                "message_id": message_id,
                "feedback_type": feedback_type,
            },
        ):
            self.feedback.create(payload)
            self.session.commit()
        answer = (
            "Resumen\n"
            "Gracias. He registrado tu feedback para mejorar futuras respuestas.\n\n"
            "Siguiente paso\n"
            "Si quieres, puedes reformular la pregunta o pedirme otro caso parecido."
        )
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
            answer = self._format_incident_created_answer(created)
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
        *,
        write_retrieval_logs: bool = True,
        retrieval_config: RetrievalConfig | None = None,
        trace_run: Any | None = None,
    ) -> dict[str, Any]:
        clarification_attempts = int(state.get("clarification_attempts", 0))
        effective_config = retrieval_config or DEFAULT_RETRIEVAL_CONFIG
        with trace_run.child(
            "rag.retrieve",
            run_type="retriever",
            inputs={
                "question": request.message,
                "retrieval_config": {
                    "top_k": effective_config.top_k,
                    "vector_weight": effective_config.vector_weight,
                    "text_weight": effective_config.text_weight,
                    "vector_candidates": effective_config.vector_candidates,
                    "text_candidates": effective_config.text_candidates,
                },
            },
        ) if trace_run else RagTrace().start_run("rag.retrieve") as retrieve_run, start_span(
            "chat.retrieve",
            {
                "conversation_id": conversation_id,
                "query.length": len(request.message),
                "retrieval.top_k": effective_config.top_k,
                "retrieval.vector_weight": effective_config.vector_weight,
                "retrieval.text_weight": effective_config.text_weight,
            },
        ) as retrieve_span:
            retrieved = self.retrieve(request.message, retrieval_config=effective_config)
            confidence = self.calculate_confidence(retrieved)
            retrieve_attrs = retrieval_span_attributes(retrieved=retrieved, confidence=confidence)
            set_span_attributes(retrieve_span, retrieve_attrs)
            retrieve_run.set_outputs(
                {
                    "confidence": confidence,
                    "retrieved_chunks": serialize_chunks_for_langsmith(retrieved),
                    "retrieved_count": len(retrieved),
                }
            )

        if not retrieved or confidence < self.settings.retrieval_confidence_threshold:
            clarification_attempts += 1
            state["clarification_attempts"] = clarification_attempts
            if clarification_attempts >= 3:
                state["offer_incident"] = True
                answer = (
                    "Resumen\n"
                    "No tengo evidencia suficiente en el indice para responder con seguridad.\n\n"
                    "Detalle\n"
                    "Con la informacion recuperada no puedo darte un procedimiento fiable sin inventar pasos.\n\n"
                    "Siguiente paso\n"
                    "Si quieres, puedo ayudarte a registrar una incidencia no resuelta para dejar trazabilidad."
                )
                self._trace_formatted_response(
                    trace_run,
                    answer=answer,
                    sources=[],
                    related_incidents=[],
                    conversation_id=conversation_id,
                    actual_behavior="abstain_and_offer_incident_registration",
                )
                latency_ms = int((time.perf_counter() - started_at) * 1000)
                if write_retrieval_logs:
                    self._write_retrieval_log(
                        conversation_id=conversation_id,
                        message_id=user_message_id,
                        query=request.message,
                        intent=intent,
                        answer=answer,
                        confidence=confidence,
                        latency_ms=latency_ms,
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
                    "_meta": {
                        "retrieved": retrieved,
                        "confidence": confidence,
                        "decision": None,
                        "context_chunks": [],
                        "actual_behavior": "abstain_and_offer_incident_registration",
                        "latency_ms": latency_ms,
                    },
                    "_state": state,
                }

            full_answer = (
                "Resumen\n"
                "Necesito un poco mas de detalle para responder con seguridad.\n\n"
                "Detalle\n"
                f"Indica el sistema, el proceso o el error exacto. Intento de aclaracion {clarification_attempts} de 2.\n\n"
                "Siguiente paso\n"
                "Por ejemplo: 'RutaNexo no cierra una ruta aprobada' o 'SafeGate rechaza un acceso temporal'."
            )
            self._trace_formatted_response(
                trace_run,
                answer=full_answer,
                sources=[],
                related_incidents=[],
                conversation_id=conversation_id,
                actual_behavior="ask_clarification",
            )
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            if write_retrieval_logs:
                self._write_retrieval_log(
                    conversation_id=conversation_id,
                    message_id=user_message_id,
                    query=request.message,
                    intent=intent,
                    answer=full_answer,
                    confidence=confidence,
                    latency_ms=latency_ms,
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
                "_meta": {
                    "retrieved": retrieved,
                    "confidence": confidence,
                    "decision": None,
                    "context_chunks": [],
                    "actual_behavior": "ask_clarification",
                    "latency_ms": latency_ms,
                },
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
        trace_context_chunks = [
            {
                "chunk_id": item.chunk_id,
                "content": item.content,
                "source_type": item.source_type,
                "source_id": item.source_id,
                "metadata": item.metadata,
            }
            for item in retrieved
        ]
        prompt_messages = build_chat_messages(
            question=request.message,
            context_chunks=trace_context_chunks,
            conversation_state=state,
        )
        with trace_run.child(
            "rag.generate_answer",
            run_type="llm",
            inputs={
                "question": request.message,
                "context_chunks": serialize_context_for_langsmith(trace_context_chunks),
                "messages": prompt_messages,
            },
        ) if trace_run else RagTrace().start_run("rag.generate_answer") as answer_run, start_span(
            "chat.generate_answer",
            {
                "conversation_id": conversation_id,
                "context_chunk_count": len(trace_context_chunks),
                "question.length": len(request.message),
            },
        ) as answer_span:
            decision, context_chunks = self.generate_answer(request.message, retrieved, state)
            answer_run.set_outputs(
                {
                    "decision": serialize_decision_for_langsmith(decision),
                    "context_chunks": serialize_context_for_langsmith(context_chunks),
                }
            )
            set_span_attributes(
                answer_span,
                {
                    "llm.needs_clarification": decision.needs_clarification,
                    "llm.should_offer_incident": decision.should_offer_incident,
                    "llm.used_chunk_ids": decision.used_chunk_ids,
                    "llm.answer_length": len(decision.answer or ""),
                },
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
        answer = self._format_answer_for_demo(decision.answer, related_incidents=related_incidents)
        self._trace_formatted_response(
            trace_run,
            answer=answer,
            sources=[source.model_dump() for source in sources],
            related_incidents=related_incidents,
            conversation_id=conversation_id,
            actual_behavior="ask_clarification" if decision.needs_clarification else "answer_with_sources",
            decision=serialize_decision_for_langsmith(decision),
        )
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        if write_retrieval_logs:
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
                latency_ms=latency_ms,
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
            "fallback_text": self._build_sources_fallback(answer, sources, related_incidents),
            "_meta": {
                "retrieved": retrieved,
                "confidence": confidence,
                "decision": decision,
                "context_chunks": context_chunks,
                "actual_behavior": "ask_clarification" if decision.needs_clarification else "answer_with_sources",
                "latency_ms": latency_ms,
            },
            "_state": state,
        }

    def _format_answer_for_demo(self, answer: str, *, related_incidents: list[dict] | None = None) -> str:
        cleaned_answer = answer.strip()
        next_step = (
            "Si quieres, puedo ampliar el procedimiento con mas detalle."
            if not related_incidents
            else "Si quieres, puedo ampliar el procedimiento o revisar las incidencias relacionadas."
        )
        lines = ["Resumen", cleaned_answer, "", "Siguiente paso", next_step]
        return "\n".join(lines)

    def _trace_response_payload(self, response: ChatResponse) -> dict[str, Any]:
        return {
            "conversation_id": response.conversation_id,
            "answer": response.answer,
            "fallback_text": response.fallback_text,
            "sources": [source.model_dump() for source in response.sources],
            "related_incidents": response.related_incidents,
            "needs_clarification": response.needs_clarification,
            "clarification_attempt": response.clarification_attempt,
            "should_offer_incident": response.should_offer_incident,
            "created_ticket_id": response.created_ticket_id,
            "created_ticket_external_id": response.created_ticket_external_id,
            "message_id": response.message_id,
        }

    def _trace_formatted_response(
        self,
        trace_run,
        *,
        answer: str,
        sources: list[dict],
        related_incidents: list[dict],
        conversation_id: int,
        actual_behavior: str,
        decision: dict[str, Any] | None = None,
    ) -> None:
        with trace_run.child(
            "rag.format_response",
            run_type="chain",
            inputs={
                "decision": decision or {},
                "sources": sources,
                "related_incidents": related_incidents,
                "actual_behavior": actual_behavior,
            },
        ) if trace_run else RagTrace().start_run("rag.format_response") as format_run, start_span(
            "chat.response",
            {
                "conversation_id": conversation_id,
                "source.count": len(sources),
                "related_incident.count": len(related_incidents),
                "actual_behavior": actual_behavior,
            },
        ) as response_span:
            format_run.set_outputs({"answer": answer, "source_count": len(sources)})
            set_span_attributes(response_span, {"answer.length": len(answer)})

    def _format_incident_created_answer(self, created: dict[str, Any]) -> str:
        lines = [
            "Resumen",
            f"Incidencia registrada e indexada correctamente: {created['external_id']}.",
            "",
            "Detalle",
            (
                f"Titulo: {created.get('title', 'Sin titulo')} | "
                f"Sistema: {created.get('affected_system', 'N/D')} | "
                f"Estado: {created.get('status', 'N/D')}"
            ),
            "",
            "Siguiente paso",
            "Ya puedes usar este ticket como referencia en futuras consultas o seguir completando contexto operativo.",
        ]
        return "\n".join(lines)

    def _build_sources_fallback(
        self,
        answer: str,
        sources: list[SourceSnippet],
        related_incidents: list[dict] | None = None,
    ) -> str:
        lines = [answer, "", "Fuentes consultadas"]
        for index, source in enumerate(sources[:5], start=1):
            lines.append(self._format_source_line(source, index=index))
        if related_incidents:
            lines.extend(["", "Incidencias relacionadas"])
            for incident in related_incidents[:3]:
                lines.append(f"- {incident['external_id']}: {incident['title']} ({incident['status']})")
        return "\n".join(lines)

    def _format_source_line(self, source: SourceSnippet, *, index: int) -> str:
        source_type = "Documento" if source.source_type == "document" else "Incidencia"
        title = source.title.strip() or f"{source_type} {source.source_id}"
        detail = source.source_url or source.excerpt.strip()
        if len(detail) > 160:
            detail = detail[:157].rstrip() + "..."
        return f"- [{index}] {source_type} {source.source_id} - {title}: {detail}"

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
