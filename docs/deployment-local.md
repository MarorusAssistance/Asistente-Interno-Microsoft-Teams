# Despliegue local

## Pasos

1. Copiar `.env.example` a `.env`.
2. Levantar el stack:

```bash
docker compose up --build
```

3. Aplicar migraciones:

```bash
uv run alembic upgrade head
```

4. Cargar datos seed:

```bash
uv run python scripts/load_seed.py
```

5. Reconstruir indice:

```bash
uv run python scripts/rebuild_index.py
```

## Endpoints utiles

- `http://localhost:8000/api/health`
- `http://localhost:8000/api/chat`
- `http://localhost:7071/incidents`
- `http://localhost:7072/index/rebuild`
