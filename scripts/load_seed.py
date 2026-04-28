from __future__ import annotations

try:
    from seed_db import main as seed_main
except ImportError:  # pragma: no cover - compatibilidad cuando se importa como paquete
    from scripts.seed_db import main as seed_main


def main() -> int:
    print("scripts/load_seed.py está deprecado; delegando en scripts/seed_db.py")
    return seed_main()


if __name__ == "__main__":
    raise SystemExit(main())
