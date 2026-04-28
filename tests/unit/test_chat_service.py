from __future__ import annotations

from types import SimpleNamespace

from internal_assistant.chat.service import ChatService
from internal_assistant.llm.mock_provider import MockLLMProvider
from internal_assistant.rag import DEFAULT_RETRIEVAL_CONFIG
from internal_assistant.rag.retrieval import RetrievedChunk
from internal_assistant.schemas.chat import ChatRequest
from tests.conftest import (
    DummySession,
    FakeConversationRepository,
    FakeFeedbackRepository,
    FakeIncidentRepository,
    FakeMessageRepository,
    FakeRetriever,
    FakeRetrievalLogsRepository,
)


def build_service(results=None):
    service = ChatService(DummySession(), llm_provider=MockLLMProvider())
    service.conversations = FakeConversationRepository()
    service.messages = FakeMessageRepository()
    service.feedback = FakeFeedbackRepository()
    service.retrieval_logs = FakeRetrievalLogsRepository()
    service.incidents = FakeIncidentRepository()
    service.retriever = FakeRetriever(results or [])
    return service


def test_low_confidence_flow_asks_for_clarification_then_offers_incident(monkeypatch):
    monkeypatch.setattr("internal_assistant.chat.service.get_settings", lambda: SimpleNamespace(retrieval_confidence_threshold=0.58, app_shared_secret="secret", custom_incidents_api_base_url="http://test", indexer_api_base_url="http://test"))
    service = build_service([])

    first = service.handle_chat(ChatRequest(user_id="u1", message="No puedo entrar"))
    second = service.handle_chat(ChatRequest(conversation_id=first.conversation_id, user_id="u1", message="Sigue igual"))
    third = service.handle_chat(ChatRequest(conversation_id=first.conversation_id, user_id="u1", message="No se"))

    assert first.needs_clarification is True
    assert second.needs_clarification is True
    assert third.should_offer_incident is True


def test_chat_response_with_sources_uses_retrieved_chunks(monkeypatch):
    monkeypatch.setattr("internal_assistant.chat.service.get_settings", lambda: SimpleNamespace(retrieval_confidence_threshold=0.10, app_shared_secret="secret", custom_incidents_api_base_url="http://test", indexer_api_base_url="http://test"))
    results = [
        RetrievedChunk(
            chunk_id=1,
            source_type="document",
            source_id=100,
            content="Para solicitar acceso temporal en SafeGate se requiere aprobacion de Seguridad.",
            metadata={"title": "Acceso temporal", "source_url": "https://example"},
            final_score=0.9,
        )
    ]
    service = build_service(results)

    response = service.handle_chat(ChatRequest(user_id="u1", message="Como solicito acceso temporal?"))

    assert response.sources
    assert response.answer.startswith("Resumen")
    assert "Fuentes consultadas" in response.fallback_text


def test_register_unresolved_incident_flow(monkeypatch):
    monkeypatch.setattr("internal_assistant.chat.service.get_settings", lambda: SimpleNamespace(retrieval_confidence_threshold=0.58, app_shared_secret="secret", custom_incidents_api_base_url="http://test", indexer_api_base_url="http://test"))
    service = build_service([])
    created = {"id": 321, "external_id": "INC-00321", "title": "Error SafeGate", "affected_system": "SafeGate", "status": "open"}
    monkeypatch.setattr(service, "_create_incident", lambda payload: created)
    monkeypatch.setattr(service, "_trigger_index_incident", lambda incident_id: None)

    third = None
    for message in ["No puedo entrar", "Sigue fallando", "No tengo mas detalle"]:
        third = service.handle_chat(ChatRequest(conversation_id=third.conversation_id if third else None, user_id="u1", message=message))

    start = service.handle_chat(ChatRequest(conversation_id=third.conversation_id, user_id="u1", message="si"))
    fill_title = service.handle_chat(ChatRequest(conversation_id=third.conversation_id, user_id="u1", message="titulo: Error SafeGate"))
    fill_description = service.handle_chat(ChatRequest(conversation_id=third.conversation_id, user_id="u1", message="descripcion: No permite acceder al torno"))
    fill_department = service.handle_chat(ChatRequest(conversation_id=third.conversation_id, user_id="u1", message="departamento: Seguridad"))
    fill_category = service.handle_chat(ChatRequest(conversation_id=third.conversation_id, user_id="u1", message="categoria: accesos"))
    fill_system = service.handle_chat(ChatRequest(conversation_id=third.conversation_id, user_id="u1", message="sistema: SafeGate"))
    fill_impact = service.handle_chat(ChatRequest(conversation_id=third.conversation_id, user_id="u1", message="impacto: bloquea el acceso de guardia"))
    fill_expected = service.handle_chat(ChatRequest(conversation_id=third.conversation_id, user_id="u1", message="esperado: deberia abrir la puerta"))
    confirm_summary = service.handle_chat(ChatRequest(conversation_id=third.conversation_id, user_id="u1", message="actual: indica acceso denegado"))
    created_response = service.handle_chat(ChatRequest(conversation_id=third.conversation_id, user_id="u1", message="si"))

    assert start.answer.startswith("Necesito el titulo")
    assert "Resumen de la incidencia" in confirm_summary.answer
    assert created_response.created_ticket_external_id == "INC-00321"
    assert created_response.created_ticket_id == 321
    assert "Incidencia registrada" in created_response.answer


def test_feedback_useful_and_not_useful_messages_are_stored(monkeypatch):
    monkeypatch.setattr("internal_assistant.chat.service.get_settings", lambda: SimpleNamespace(retrieval_confidence_threshold=0.58, app_shared_secret="secret", custom_incidents_api_base_url="http://test", indexer_api_base_url="http://test"))
    service = build_service([])

    useful = service.handle_chat(ChatRequest(user_id="u1", message="util gracias"))
    not_useful = service.handle_chat(ChatRequest(conversation_id=useful.conversation_id, user_id="u1", message="no util no me ayudo"))

    assert useful.answer.startswith("Resumen")
    assert len(service.feedback.items) == 2


def test_handle_chat_uses_default_retrieval_config(monkeypatch):
    monkeypatch.setattr("internal_assistant.chat.service.get_settings", lambda: SimpleNamespace(retrieval_confidence_threshold=0.10, app_shared_secret="secret", custom_incidents_api_base_url="http://test", indexer_api_base_url="http://test"))
    service = build_service([])

    class CapturingRetriever:
        def __init__(self):
            self.config = None

        def search(self, query, query_embedding, limit=5, config=None):
            self.config = config
            return [
                RetrievedChunk(
                    chunk_id=1,
                    source_type="document",
                    source_id=100,
                    content="LogiCore ERP requiere trazabilidad operativa.",
                    metadata={"title": "Control operativo", "source_url": "https://example"},
                    final_score=0.9,
                )
            ]

    retriever = CapturingRetriever()
    service.retriever = retriever

    service.handle_chat(ChatRequest(user_id="u1", message="Como se controla un pedido intercentro?"))

    assert retriever.config is not None
    assert retriever.config.top_k == DEFAULT_RETRIEVAL_CONFIG.top_k
    assert retriever.config.vector_weight == DEFAULT_RETRIEVAL_CONFIG.vector_weight
    assert retriever.config.text_weight == DEFAULT_RETRIEVAL_CONFIG.text_weight
