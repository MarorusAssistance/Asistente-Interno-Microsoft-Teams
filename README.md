# Internal Assistant MVP

Asistente conversacional interno para Microsoft Teams orientado a una empresa ficticia de logistica. El proyecto funciona en local y queda preparado para una demo reproducible en Azure con Teams como custom app.

## Que hace

- Responde preguntas internas con RAG sobre documentacion privada e incidencias.
- Muestra fuentes y fragmentos usados.
- Pide aclaraciones cuando no encuentra evidencia suficiente.
- Propone y registra incidencias nuevas.
- Guarda conversaciones, feedback y `retrieval_logs`.
- Expone `/api/messages` para Bot Framework / Teams.

## Estructura

- `app-service/`: FastAPI principal.
- `functions/custom-incidents-api-function/`: sistema fuente simulado.
- `functions/indexer-function/`: indexado y embeddings.
- `src/internal_assistant/`: dominio compartido.
- `infra/`: Bicep modular para Azure.
- `teams-app/`: manifiesto e iconos para Teams.

## Local

1. Copiar variables:

```bash
cp .env.example .env
```

2. Elegir provider:

```env
LLM_PROVIDER=mock
EMBEDDINGS_PROVIDER=mock
EMBEDDING_DIMENSIONS=512
```

o:

```env
LLM_PROVIDER=openai
EMBEDDINGS_PROVIDER=openai
OPENAI_API_KEY=sk-...
CHAT_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=512
```

3. Levantar el flujo local:

```bash
python -m uv sync
docker compose up postgres
python scripts/init_db.py
python scripts/validate_seed_data.py
python scripts/seed_db.py
python scripts/rebuild_index.py
python scripts/check_index.py
uv run uvicorn main:app --app-dir app-service --host 0.0.0.0 --port 8000
uv run uvicorn local_main:app --app-dir functions/custom-incidents-api-function --host 0.0.0.0 --port 7071
uv run uvicorn local_main:app --app-dir functions/indexer-function --host 0.0.0.0 --port 7072
```

4. Probar chat:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "u-demo",
    "message": "Como se registra una entrega parcial en ventana critica en LogiCore ERP?"
  }'
```

## Azure

1. Copiar `.env.azure.example` a `.env.azure`.
2. Rellenar secretos y nombres.
3. Ejecutar:

```bash
./scripts/azure_login_check.sh
./scripts/deploy_infra.sh
./scripts/configure_app_settings.sh
./scripts/deploy_app_service.sh
./scripts/deploy_functions.sh
./scripts/seed_cloud_db.sh
./scripts/rebuild_cloud_index.sh
./scripts/check_cloud_index.sh
./scripts/smoke_test_cloud.sh
```

## Teams

1. Configurar `MICROSOFT_APP_ID`, `MICROSOFT_APP_PASSWORD`, `MICROSOFT_APP_TENANT_ID`, `TEAMS_APP_ID` y `BOT_ENDPOINT`.
2. Generar el paquete:

```bash
./scripts/package_teams_app.sh
```

3. Subir `teams-app/build/internal-assistant-demo.zip` como custom app en Teams.

## GitHub Actions

Workflows incluidos:

- `.github/workflows/deploy-infra.yml`
- `.github/workflows/deploy-app-service.yml`
- `.github/workflows/deploy-functions.yml`

Secrets esperados:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_RESOURCE_GROUP`
- `POSTGRES_ADMIN_PASSWORD`
- `OPENAI_API_KEY`
- `ADMIN_API_KEY`
- `APP_SHARED_SECRET`
- `MICROSOFT_APP_ID`
- `MICROSOFT_APP_PASSWORD`
- `MICROSOFT_APP_TENANT_ID`

Los workflows usan `azure/login` con OIDC.

## Documentacion

- `docs/deployment-local.md`
- `docs/deployment-azure.md`
- `docs/teams-setup.md`
- `docs/architecture.md`
- `docs/cost-control.md`
- `docs/demo-script.md`
- `docs/rag-evaluation.md`

## Limitaciones

- `AzureOpenAIProvider` sigue preparado pero no activo.
- No hay SSO real ni RBAC por departamentos.
- No se usa Key Vault en v0.2.
- La app de Teams requiere tenant con sideloading o custom apps habilitado.

## Testing

```bash
python -m uv run pytest -q
```

## Evaluacion RAG

El repo incluye un framework de evaluacion reproducible bajo `evaluation/` para medir retrieval, calidad de respuesta, cobertura de fuentes, abstencion y robustez adversarial.

Comandos principales:

```bash
python scripts/run_rag_eval.py --provider mock
python scripts/run_rag_eval.py --provider openai --include-adversarial
python scripts/compare_retrieval_configs.py
```

Variables utiles en `.env`:

- `EVAL_USE_LLM_JUDGE=false`
- `EVAL_DATASET_PATH=evaluation/datasets/rag_eval_questions.json`
- `EVAL_OUTPUT_DIR=evaluation/reports`
- `EVAL_TOP_K=5`
- `EVAL_VECTOR_WEIGHT=0.70`
- `EVAL_TEXT_WEIGHT=0.30`
- `EVAL_PROVIDER=mock`

Mas detalle en `docs/rag-evaluation.md`.
