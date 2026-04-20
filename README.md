# Internal Assistant MVP

Asistente conversacional interno para Microsoft Teams orientado a una empresa ficticia de logistica. El objetivo es servir como portfolio tecnico con una base que pueda evolucionar a una demo comercial sobre Azure.

## Que hace el proyecto

- Responde preguntas internas usando RAG sobre documentacion privada e incidencias internas.
- Muestra fuentes con enlace si existe y, si no, con fragmentos textuales.
- Pide hasta 2 aclaraciones cuando la evidencia recuperada no es suficiente.
- Propone registrar una incidencia no resuelta cuando sigue sin poder responder con confianza.
- Permite registrar incidencias resueltas y no resueltas mediante el bot.
- Persiste conversaciones, mensajes, feedback y logs de recuperacion.
- Integra un endpoint preparado para Microsoft Teams / Bot Framework.

## Arquitectura del MVP

- `app-service/`: FastAPI principal desplegable en Azure App Service.
- `functions/custom-incidents-api-function/`: Azure Function que simula el sistema fuente de incidencias.
- `functions/indexer-function/`: Azure Function para chunking, embeddings e indexado.
- `src/internal_assistant/`: libreria compartida con dominio, configuracion, RAG, providers, seguridad y cards.
- `data/`: dataset inicial de tickets y documentos en espanol.

La documentacion ampliada esta en:

- `docs/architecture.md`
- `docs/deployment-local.md`
- `docs/deployment-azure.md`
- `docs/demo-script.md`
- `docs/cost-control.md`

## Requisitos

- Docker y Docker Compose
- Python 3.10 o superior
- `uv` para desarrollo local
- Clave de OpenAI para embeddings y chat en ejecucion real

## Como levantarlo en local

1. Copiar variables:

   ```bash
   cp .env.example .env
   ```

2. Levantar infraestructura y servicios:

   ```bash
   docker compose up --build
   ```

3. Inicializar base de datos:

   ```bash
   uv run python scripts/init_db.py
   ```

4. Cargar seed data:

   ```bash
   uv run python scripts/load_seed.py
   ```

5. Reconstruir el indice:

   ```bash
   uv run python scripts/rebuild_index.py
   ```

## Base de datos y migraciones

- Crear o actualizar el esquema:

  ```bash
  uv run alembic upgrade head
  ```

- La extension `vector` se habilita automaticamente desde la capa de inicializacion y desde las migraciones.

## Como probar `/api/chat`

Ejemplo con `curl`:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "u-demo",
    "message": "Como solicito acceso temporal a SafeGate para personal externo?"
  }'
```

La respuesta incluye:

- `answer`
- `sources`
- `related_incidents`
- `needs_clarification`
- `should_offer_incident`
- `fallback_text`

## Como preparar el paquete de Teams

1. Revisar `teams-app/manifest.json`.
2. Sustituir los placeholders de bot id, dominios validos e iconos.
3. Comprimir `manifest.json`, `color.png` y `outline.png` en un zip.
4. Importarlo en Microsoft Teams como app personalizada.

## Flujo de seed data

- `data/seed_tickets.json`: 100 tickets, 90 resueltos y 10 no resueltos.
- `data/seed_documents.json`: 20 documentos internos.
- Los tickets se crean a traves de la `custom-incidents-api-function`.
- Los documentos se insertan directamente en PostgreSQL.

## Limitaciones del MVP

- No incluye front-end web dedicado.
- `AzureOpenAIProvider` queda preparado, pero el camino activo usa OpenAI API.
- La integracion de Teams esta lista a nivel tecnico, pero requiere registrar el bot para una prueba real en el canal.
- No hay Bicep todavia; solo documentacion placeholder en `infra/`.

## Estrategia de costes

- Embeddings de 512 dimensiones con `text-embedding-3-small`.
- Recuperacion hibrida sin reranking avanzado.
- Dataset local y arquitectura modular para activar Azure OpenAI y Application Insights en una segunda fase.
- Recomendaciones detalladas en `docs/cost-control.md`.

## Testing

Ejecutar tests:

```bash
uv run pytest
```

Los tests usan `MockLLMProvider` y cubren chunking, embeddings mock, recuperacion hibrida, flujos de baja confianza, registro de incidencias, feedback y proteccion de endpoints.
