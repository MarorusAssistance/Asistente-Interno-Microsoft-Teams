from __future__ import annotations

import subprocess

from sqlalchemy import text

from internal_assistant.db import session_scope


def main() -> None:
    with session_scope() as session:
        session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    subprocess.run(["uv", "run", "alembic", "upgrade", "head"], check=True)
    print("Base de datos inicializada y migraciones aplicadas.")


if __name__ == "__main__":
    main()
