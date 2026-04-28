from __future__ import annotations

import subprocess
import sys
import os

from sqlalchemy import text

from internal_assistant.config import get_settings
from internal_assistant.db import session_scope


def main() -> None:
    settings = get_settings()
    with session_scope() as session:
        session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    env = os.environ.copy()
    env["EMBEDDING_DIMENSIONS"] = str(settings.embedding_dimensions)
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True, env=env)
    print("Base de datos inicializada y migraciones aplicadas.")


if __name__ == "__main__":
    main()
