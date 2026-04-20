from __future__ import annotations

import json

import pytest

from internal_assistant.seed_data import (
    DOCUMENTS_FILE,
    TICKETS_FILE,
    SeedDataValidationError,
    build_seed_documents,
    build_seed_tickets,
    validate_seed_data,
    validate_seed_files,
)


def _write_seed_files(tmp_path, tickets, documents):
    (tmp_path / TICKETS_FILE).write_text(json.dumps(tickets, ensure_ascii=False, indent=2), encoding="utf-8")
    (tmp_path / DOCUMENTS_FILE).write_text(json.dumps(documents, ensure_ascii=False, indent=2), encoding="utf-8")


def test_validate_seed_data_accepts_expected_dataset():
    summary = validate_seed_data(build_seed_tickets(), build_seed_documents())

    assert summary.tickets == 100
    assert summary.resolved_tickets == 90
    assert summary.unresolved_tickets == 10
    assert summary.documents == 20


def test_validate_seed_data_detects_wrong_ticket_count(tmp_path):
    tickets = build_seed_tickets()[:-1]
    documents = build_seed_documents()
    _write_seed_files(tmp_path, tickets, documents)

    with pytest.raises(SeedDataValidationError, match="100 tickets"):
        validate_seed_files(tmp_path)


def test_validate_seed_data_detects_resolved_ticket_without_resolution(tmp_path):
    tickets = build_seed_tickets()
    documents = build_seed_documents()
    tickets[0]["resolution"] = ""
    _write_seed_files(tmp_path, tickets, documents)

    with pytest.raises(SeedDataValidationError, match="resolution"):
        validate_seed_files(tmp_path)


def test_validate_seed_data_detects_short_document(tmp_path):
    tickets = build_seed_tickets()
    documents = build_seed_documents()
    documents[0]["content"] = "Texto demasiado corto"
    _write_seed_files(tmp_path, tickets, documents)

    with pytest.raises(SeedDataValidationError, match="500 caracteres"):
        validate_seed_files(tmp_path)
