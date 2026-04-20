from __future__ import annotations

import sys
from pathlib import Path

from internal_assistant.seed_data import DATA_DIR, SeedDataValidationError, validate_seed_files


def run_validation(data_dir: Path = DATA_DIR) -> int:
    summary = validate_seed_files(data_dir)
    print(f"Tickets: {summary.tickets}")
    print(f"Tickets resueltos: {summary.resolved_tickets}")
    print(f"Tickets no resueltos: {summary.unresolved_tickets}")
    print(f"Documentos: {summary.documents}")
    print(f"Distribución documentos: {summary.document_distribution}")
    print("Validación: OK")
    return 0


def main() -> int:
    try:
        return run_validation()
    except SeedDataValidationError as exc:
        print(f"Validación: ERROR - {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
