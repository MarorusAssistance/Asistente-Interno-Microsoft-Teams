from __future__ import annotations

from pydantic import BaseModel, Field


class SourceSnippet(BaseModel):
    source_type: str
    source_id: int
    title: str
    source_url: str | None = None
    excerpt: str
    chunk_id: int


class AssistantDecision(BaseModel):
    answer: str
    needs_clarification: bool = False
    clarification_question: str | None = None
    should_offer_incident: bool = False
    used_chunk_ids: list[int] = Field(default_factory=list)


class ChatRequest(BaseModel):
    conversation_id: int | None = None
    user_id: str
    message: str
    channel: str = "local"
    teams_conversation_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: int
    answer: str
    sources: list[SourceSnippet] = Field(default_factory=list)
    related_incidents: list[dict] = Field(default_factory=list)
    needs_clarification: bool = False
    clarification_attempt: int = 0
    should_offer_incident: bool = False
    adaptive_card: dict | None = None
    fallback_text: str
    created_ticket_id: int | None = None
    created_ticket_external_id: str | None = None
    message_id: int | None = None
