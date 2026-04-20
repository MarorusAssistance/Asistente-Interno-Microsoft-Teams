# Despliegue Azure

## Prerrequisitos

- Azure CLI autenticado con permisos sobre el Resource Group objetivo.
- Python 3.12 y `uv`.
- Un Resource Group existente o permiso para crearlo.
- Una app registration para el bot con `MICROSOFT_APP_ID` y `MICROSOFT_APP_PASSWORD`.
- OpenAI API key valida.

## Variables

1. Copia `.env.azure.example` a `.env.azure`.
2. Rellena al menos:

```env
PROJECT_NAME=internal-assistant
ENVIRONMENT_NAME=demo
AZURE_LOCATION=westeurope
AZURE_RESOURCE_GROUP=rg-internal-assistant-demo
AZURE_SUBSCRIPTION_ID=<subscription-id>
POSTGRES_ADMIN_USER=pgadmininternal
POSTGRES_ADMIN_PASSWORD=<password>
POSTGRES_DATABASE_NAME=assistant
OPENAI_API_KEY=<openai-key>
CHAT_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=512
ADMIN_API_KEY=<admin-key>
APP_SHARED_SECRET=<shared-secret>
MICROSOFT_APP_ID=<bot-app-id>
MICROSOFT_APP_PASSWORD=<bot-secret>
TEAMS_APP_ID=<teams-app-id>
```

## Flujo completo

1. Validar login:

```bash
./scripts/azure_login_check.sh
```

2. Desplegar infraestructura:

```bash
./scripts/deploy_infra.sh
```

3. Configurar App Settings y startup command:

```bash
./scripts/configure_app_settings.sh
```

4. Desplegar App Service:

```bash
./scripts/deploy_app_service.sh
```

5. Desplegar Azure Functions:

```bash
./scripts/deploy_functions.sh
```

6. Aplicar migraciones contra PostgreSQL cloud:

```bash
export DATABASE_URL="$(python -m uv run python - <<'PY'
from internal_assistant.runtime import build_azure_postgres_url
import os
print(build_azure_postgres_url(
    server_name=os.environ["AZURE_POSTGRES_SERVER_NAME"],
    database_name=os.environ["POSTGRES_DATABASE_NAME"],
    admin_user=os.environ["POSTGRES_ADMIN_USER"],
    password=os.environ["POSTGRES_ADMIN_PASSWORD"],
))
PY
)"
python -m uv run alembic upgrade head
```

7. Cargar dataset cloud:

```bash
./scripts/seed_cloud_db.sh
./scripts/rebuild_cloud_index.sh
./scripts/check_cloud_index.sh
```

8. Smoke test:

```bash
./scripts/smoke_test_cloud.sh
```

## Health checks esperados

- `GET /api/health`
- `GET /api/health/deep`
- `GET https://<indexer>.azurewebsites.net/api/health`
- `GET https://<incidents>.azurewebsites.net/api/health`

`/api/health/deep` valida:

- conectividad con PostgreSQL
- configuracion del provider
- existencia de chunks
- extension `vector`

## pgvector en Azure PostgreSQL

El servidor Flexible Server queda configurado con `azure.extensions=vector`. Despues:

1. Aplica migraciones.
2. Ejecuta `CREATE EXTENSION IF NOT EXISTS vector;` usando `scripts/init_db.py` o Alembic.
3. Verifica el indice con `./scripts/check_cloud_index.sh`.

## Smoke test funcional

Ejemplo de consulta cloud:

```bash
curl -X POST "https://<webapp>.azurewebsites.net/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "u-demo",
    "message": "Como se registra una entrega parcial en ventana critica en LogiCore ERP?"
  }'
```

## GitHub Secrets necesarios

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

Los workflows usan `azure/login` con OIDC. No usan publish profiles.
