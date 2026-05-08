# Despliegue Azure

## Objetivo

Publicar una demo reproducible en Azure con App Service, Azure Functions, PostgreSQL Flexible Server y Azure Bot, manteniendo costes contenidos.

## Prerrequisitos

- Azure CLI autenticado
- permisos sobre la suscripcion o el Resource Group objetivo
- Python 3.12 y `uv`
- app registration para el bot
- OpenAI API key valida

## Preparacion

1. Copia `.env.azure.example` a `.env.azure`.
2. Rellena como minimo:

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
MICROSOFT_APP_TENANT_ID=<entra-tenant-id>
TEAMS_APP_ID=<teams-app-id>
```

Opcional para trazabilidad de calidad RAG:

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=<langsmith-api-key>
LANGSMITH_PROJECT=internal-assistant-mvp
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

`Application Insights` no usa API key en la app. La Web App recibe `APPLICATIONINSIGHTS_CONNECTION_STRING` desde la infraestructura y emite spans operativos sin prompts ni chunks completos.

## Despliegue manual

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
./scripts/demo_prep.sh cloud
./scripts/demo_health_check.sh cloud
```

Si activas LangSmith despues de desplegar infraestructura, vuelve a ejecutar:

```bash
./scripts/configure_app_settings.sh
./scripts/deploy_app_service.sh
```

Luego lanza una pregunta desde `/demo` o `/api/chat` y busca un trace `rag.chat` en el proyecto LangSmith configurado.

## Health checks esperados

- `GET /api/health`
- `GET /api/health/deep`
- `GET https://<indexer>.azurewebsites.net/api/health`
- `GET https://<incidents>.azurewebsites.net/api/health`

`/api/health/deep` debe confirmar:

- conectividad con PostgreSQL
- provider configurado
- presencia de chunks
- extension `vector`

## Migraciones y pgvector

Si necesitas ejecutar migraciones manuales contra la base cloud:

```bash
python -m uv run alembic upgrade head
```

El servidor Flexible Server queda preparado para `pgvector`, pero conviene verificarlo siempre con `scripts/check_cloud_index.sh`.

## Prueba funcional

Sin Teams, puedes validar la Web App desde la UI integrada:

```text
https://<webapp>.azurewebsites.net/demo
```

La consola usa la misma API publicada bajo `/api`, muestra fuentes y permite feedback. Es la ruta recomendada para probar cloud cuando no tienes un tenant de Teams preparado.

Tambien puedes llamar la API directamente:

```bash
curl -X POST "https://<webapp>.azurewebsites.net/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "u-demo",
    "message": "Como se registra una entrega parcial en ventana critica en LogiCore ERP?"
  }'
```

## Cierre de costes tras la demo

```bash
./scripts/stop_postgres_azure.sh
```

Si quieres coste casi cero, la opcion mas segura es borrar el Resource Group completo cuando acabes.
