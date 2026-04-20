from __future__ import annotations

from typing import Annotated

from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import Activity
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from internal_assistant.chat import ChatService
from internal_assistant.config import get_settings
from internal_assistant.db import get_session
from internal_assistant.observability import configure_logging
from internal_assistant.repositories import DocumentRepository, IncidentRepository
from internal_assistant.schemas import ChatRequest, ChatResponse, DocumentRead, FeedbackCreate, IncidentRead

configure_logging()
settings = get_settings()
app = FastAPI(title="internal-assistant-mvp", version="0.1.0")


class TeamsAssistantBot(ActivityHandler):
    def __init__(self, service: ChatService) -> None:
        self.service = service

    async def on_message_activity(self, turn_context: TurnContext):
        response = self.service.handle_chat(
            ChatRequest(
                user_id=turn_context.activity.from_property.id or "teams-user",
                message=turn_context.activity.text or "",
                channel=turn_context.activity.channel_id or "msteams",
                teams_conversation_id=turn_context.activity.conversation.id if turn_context.activity.conversation else None,
            )
        )
        await turn_context.send_activity(response.fallback_text)


DbSession = Annotated[Session, Depends(get_session)]


@app.get("/api/health")
def health(session: DbSession) -> dict:
    session.execute(text("SELECT 1"))
    return {"status": "ok", "service": settings.app_name}


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, session: DbSession) -> ChatResponse:
    service = ChatService(session)
    return service.handle_chat(payload)


@app.post("/api/messages")
def messages(payload: dict, session: DbSession) -> dict:
    activity = Activity().deserialize(payload)
    service = ChatService(session)
    bot = TeamsAssistantBot(service)

    if (activity.type or "").lower() != "message":
        return {"status": "ignored", "reason": "Solo se procesan actividades de tipo message en el MVP"}

    response = service.handle_chat(
        ChatRequest(
            user_id=(activity.from_property.id if activity.from_property else "teams-user"),
            message=activity.text or "",
            channel=activity.channel_id or "msteams",
            teams_conversation_id=(activity.conversation.id if activity.conversation else None),
        )
    )
    return {
        "status": "ok",
        "botbuilder_handler": bot.__class__.__name__,
        "response": response.model_dump(),
    }


@app.get("/api/tickets", response_model=list[IncidentRead])
def get_tickets(session: DbSession) -> list[IncidentRead]:
    return [IncidentRead.model_validate(item) for item in IncidentRepository(session).list()]


@app.get("/api/tickets/{ticket_id}", response_model=IncidentRead)
def get_ticket(ticket_id: int, session: DbSession) -> IncidentRead:
    incident = IncidentRepository(session).get(ticket_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return IncidentRead.model_validate(incident)


@app.get("/api/documents", response_model=list[DocumentRead])
def get_documents(session: DbSession) -> list[DocumentRead]:
    return [DocumentRead.model_validate(item) for item in DocumentRepository(session).list()]


@app.post("/api/feedback")
def save_feedback(payload: FeedbackCreate, session: DbSession) -> dict:
    service = ChatService(session)
    service.save_feedback(payload)
    return {"status": "stored"}
