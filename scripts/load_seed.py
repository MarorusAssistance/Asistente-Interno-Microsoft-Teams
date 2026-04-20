from __future__ import annotations

import json
from pathlib import Path

import httpx
from sqlalchemy import select

from internal_assistant.config import get_settings
from internal_assistant.db import session_scope
from internal_assistant.models import Document


ROOT = Path(__file__).resolve().parents[1]


def load_documents() -> int:
    documents = json.loads((ROOT / "data" / "seed_documents.json").read_text(encoding="utf-8"))
    with session_scope() as session:
        existing_titles = {title for title in session.execute(select(Document.title)).scalars().all()}
        created = 0
        for item in documents:
            if item["title"] in existing_titles:
                continue
            session.add(Document(**item))
            created += 1
        return created


def load_tickets() -> int:
    settings = get_settings()
    tickets = json.loads((ROOT / "data" / "seed_tickets.json").read_text(encoding="utf-8"))
    headers = {"x-app-shared-secret": settings.app_shared_secret}
    created = 0
    with httpx.Client(timeout=30) as client:
        for ticket in tickets:
            response = client.post(f"{settings.custom_incidents_api_base_url}/incidents", json=ticket, headers=headers)
            response.raise_for_status()
            created += 1
    return created


def main() -> None:
    documents = load_documents()
    tickets = load_tickets()
    print(f"Documentos cargados: {documents}")
    print(f"Tickets cargados: {tickets}")


if __name__ == "__main__":
    main()
