# Despliegue local

## Pasos

1. Copiar `.env.example` a `.env`.
2. Elegir el provider:

```env
LLM_PROVIDER=mock
EMBEDDINGS_PROVIDER=mock
EMBEDDING_DIMENSIONS=512
```

o bien:

```env
LLM_PROVIDER=openai
EMBEDDINGS_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

o bien:

```env
LLM_PROVIDER=openai_compatible
EMBEDDINGS_PROVIDER=openai_compatible
LLM_BASE_URL=http://host.docker.internal:11434/v1
LLM_API_KEY=local-dev-key
CHAT_MODEL=<tu-modelo-chat>
EMBEDDING_MODEL=<tu-modelo-embedding>
EMBEDDING_DIMENSIONS=<dimension-real-del-modelo>
```

3. Instalar dependencias:

```bash
python -m uv sync
```

4. Levantar PostgreSQL:

```bash
docker compose up postgres
```

5. Aplicar migraciones:

```bash
python scripts/init_db.py
```

6. Validar dataset:

```bash
python scripts/validate_seed_data.py
```

7. Seed raw:

```bash
python scripts/seed_db.py
```

8. Reconstruir indice:

```bash
python scripts/rebuild_index.py
```

9. Verificar indice:

```bash
python scripts/check_index.py
```

10. Levantar servicios HTTP:

```bash
uv run uvicorn main:app --app-dir app-service --host 0.0.0.0 --port 8000
uv run uvicorn local_main:app --app-dir functions/custom-incidents-api-function --host 0.0.0.0 --port 7071
uv run uvicorn local_main:app --app-dir functions/indexer-function --host 0.0.0.0 --port 7072
```

11. Probar `/api/chat`:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "u-demo",
    "message": "Como solicito acceso temporal a SafeGate para personal externo?"
  }'
```

Si ejecutas el modelo local en tu host y la API en Docker, usa `host.docker.internal` como hostname en `LLM_BASE_URL`.

12. Verificar health checks:

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/health/deep
curl http://localhost:7071/health
curl http://localhost:7072/health
```

## Modo host

Si prefieres ejecutar FastAPI y las Functions en tu equipo sin contenedores, puedes seguir usando PostgreSQL local y el dataset ya cargado:

```bash
uv run uvicorn main:app --app-dir app-service --host 0.0.0.0 --port 8000
uv run uvicorn local_main:app --app-dir functions/custom-incidents-api-function --host 0.0.0.0 --port 7071
uv run uvicorn local_main:app --app-dir functions/indexer-function --host 0.0.0.0 --port 7072
```

## Endpoints utiles

- `http://localhost:8000/api/health`
- `http://localhost:8000/api/health/deep`
- `http://localhost:8000/api/chat`
- `http://localhost:7071/health`
- `http://localhost:7072/health`
- `http://localhost:7071/incidents`
- `http://localhost:7072/index/rebuild`
