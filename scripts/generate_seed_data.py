from __future__ import annotations

from internal_assistant.seed_data import write_seed_files


def main() -> None:
    tickets_path, documents_path = write_seed_files()
    print(f"Dataset de tickets generado en {tickets_path}")
    print(f"Dataset de documentos generado en {documents_path}")


if __name__ == "__main__":
    main()
