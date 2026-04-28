# Internal Assistant MVP

![Python](https://img.shields.io/badge/python-3.12-blue)
![Tests](https://img.shields.io/badge/tests-pytest-green)
![Status](https://img.shields.io/badge/status-MVP%20%2F%20Demo--ready-6f42c1)

Asistente conversacional interno orientado a una empresa ficticia de logistica. El proyecto combina RAG hibrido, PostgreSQL + pgvector, registro de incidencias y una ruta de despliegue preparada para Azure y Microsoft Teams. La meta no es solo que el asistente "responda", sino que pueda explicarse, evaluarse y mostrarse con criterio tecnico en una demo o portfolio.

## Que demuestra este proyecto

- diseno de un asistente interno con RAG sobre documentacion privada e incidencias
- separacion entre sistema fuente y indice de retrieval
- busqueda hibrida con PostgreSQL full-text + pgvector
- trazabilidad de fuentes y fragmentos usados
- flujo de aclaraciones cuando la evidencia no basta
- registro de incidencias nuevas y reindexado posterior
- evaluacion tecnica del RAG con metricas y reportes
- despliegue Azure-ready con App Service, Functions y PostgreSQL
- integracion con Teams como custom app

## Problema que resuelve

En una operacion interna es habitual que el conocimiento este repartido entre procedimientos, tickets resueltos y experiencia informal del equipo. Este proyecto simula un asistente que concentra ese conocimiento en un unico punto de consulta, pero manteniendo dos limites importantes: solo responde con evidencia recuperada y, cuando no la tiene, pide aclaracion o propone registrar una incidencia nueva.

## Que demuestra tecnicamente

- modelado de un flujo RAG con chunking, embeddings y retrieval hibrido
- persistencia y observabilidad basicas con PostgreSQL
- desacoplo entre sistema fuente de incidencias y capa de indexado
- evaluacion reproducible de retrieval, respuesta, citas y abstencion
- operacion en dos rutas equivalentes:
  - local-first para desarrollo y pruebas baratas
  - Azure + Teams para demo cloud

## Arquitectura resumida

- `app-service/`: FastAPI principal con `/api/chat`, `/api/messages`, health checks, feedback y endpoints de consulta.
- `functions/custom-incidents-api-function/`: sistema fuente simulado para incidencias.
- `functions/indexer-function/`: reindexado HTTP y mantenimiento de chunks/embeddings.
- `src/internal_assistant/`: dominio compartido, providers LLM, RAG, cards, runtime y repositorios.
- `PostgreSQL + pgvector`: persistencia de incidents, documents, chunks, conversations, feedback y retrieval logs.
- `evaluation/`: datasets, judges, runners y reportes para medir calidad RAG.
- `teams-app/`: manifiesto y paquete de Teams para la demo cloud.

Mas detalle en [docs/architecture.md](/c:/Users/maror/Projects/Personal/Asistente-Interno-Microsoft-Teams/docs/architecture.md).

## Stack tecnologico

- Python 3.12
- FastAPI
- Azure Functions Python
- PostgreSQL + pgvector
- SQLAlchemy + Alembic
- Pydantic
- pytest
- Docker Compose
- OpenAI API como provider cloud inicial
- provider local `openai_compatible` para LM Studio, Ollama o similar
- Azure App Service, Azure Functions, Azure Bot y PostgreSQL Flexible Server

## Funcionalidades principales

- responder preguntas internas con RAG sobre documentos e incidencias
- citar fuentes y mostrar fragmentos de apoyo
- pedir hasta dos aclaraciones cuando la consulta es ambigua o debil
- ofrecer registrar incidencia si no hay evidencia suficiente
- registrar incidencias nuevas contra un sistema fuente simulado
- reindexar conocimiento nuevo para consultas posteriores
- guardar historial conversacional, feedback y retrieval logs
- evaluar retrieval, respuestas, citas, abstencion y casos adversariales

## Flujo funcional del asistente

1. El usuario pregunta desde `/api/chat` o Teams.
2. El servicio genera embeddings de la consulta y ejecuta retrieval hibrido.
3. El modelo responde usando solo el contexto recuperado.
4. La respuesta se presenta con estructura corta y fuentes consultadas.
5. Si la evidencia no basta, el asistente pide aclaracion.
6. Tras dos aclaraciones fallidas, propone registrar una incidencia no resuelta.
7. Cuando se crea un ticket, el sistema fuente lo guarda y el indexer lo incorpora al indice.

## Como lo pruebo yo ahora

### Ruta local

```bash
python -m uv sync
docker compose up -d postgres
python -m uv run python scripts/init_db.py
python -m uv run python scripts/seed_db.py
python -m uv run python scripts/rebuild_index.py
./scripts/demo_prep.sh local
./scripts/demo_health_check.sh local
python -m uv run uvicorn main:app --app-dir app-service --host 0.0.0.0 --port 8000
```

### Ruta Azure / Teams

```bash
./scripts/deploy_infra.sh
./scripts/configure_app_settings.sh
./scripts/deploy_app_service.sh
./scripts/deploy_functions.sh
./scripts/seed_cloud_db.sh
./scripts/rebuild_cloud_index.sh
./scripts/check_cloud_index.sh
./scripts/demo_prep.sh cloud
./scripts/demo_health_check.sh cloud
./scripts/package_teams_app.sh
```

## Como ejecutarlo en local

1. Copia [`.env.example`](/c:/Users/maror/Projects/Personal/Asistente-Interno-Microsoft-Teams/.env.example) a `.env`.
2. Elige uno de estos modos:
   - `mock` para smoke tests baratos
   - `openai` para OpenAI real
   - `openai_compatible` para LM Studio, Ollama o un endpoint OpenAI-compatible
3. Instala dependencias:

```bash
python -m uv sync
```

4. Levanta PostgreSQL:

```bash
docker compose up -d postgres
```

5. Inicializa datos e indice:

```bash
python -m uv run python scripts/init_db.py
python -m uv run python scripts/validate_seed_data.py
python -m uv run python scripts/seed_db.py
python -m uv run python scripts/rebuild_index.py
python -m uv run python scripts/check_index.py
```

Guia ampliada en [docs/deployment-local.md](/c:/Users/maror/Projects/Personal/Asistente-Interno-Microsoft-Teams/docs/deployment-local.md).

## Como poblar datos y reconstruir el indice

- validar dataset:

```bash
python -m uv run python scripts/validate_seed_data.py
```

- cargar datos raw:

```bash
python -m uv run python scripts/seed_db.py
```

- reconstruir indice:

```bash
python -m uv run python scripts/rebuild_index.py
```

- verificar indice:

```bash
python -m uv run python scripts/check_index.py
```

## Como probarlo sin Teams

Arranca FastAPI en local:

```bash
python -m uv run uvicorn main:app --app-dir app-service --host 0.0.0.0 --port 8000
```

Consulta de ejemplo:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "u-demo",
    "message": "Como solicito acceso temporal a SafeGate para personal externo?"
  }'
```

## Como probarlo en Teams

1. Configura `MICROSOFT_APP_ID`, `MICROSOFT_APP_PASSWORD`, `MICROSOFT_APP_TENANT_ID`, `TEAMS_APP_ID` y `BOT_ENDPOINT`.
2. Genera el paquete:

```bash
./scripts/package_teams_app.sh
```

3. Sube `teams-app/build/internal-assistant-demo.zip` como custom app en tu tenant.

Guia completa en [docs/teams-setup.md](/c:/Users/maror/Projects/Personal/Asistente-Interno-Microsoft-Teams/docs/teams-setup.md).

## Como ejecutar evaluacion RAG

Smoke test con mock:

```bash
python -m uv run python scripts/run_rag_eval.py --provider mock
```

Evaluacion con OpenAI y judge LLM:

```bash
python -m uv run python scripts/run_rag_eval.py --provider openai --include-adversarial --use-llm-judge
```

Comparacion de configuraciones de retrieval:

```bash
python -m uv run python scripts/compare_retrieval_configs.py
```

Los reportes quedan en `evaluation/reports/` como archivos JSON y Markdown. No se envian a Table Storage ni a otro artifact remoto por defecto.

Mas detalle en [docs/rag-evaluation.md](/c:/Users/maror/Projects/Personal/Asistente-Interno-Microsoft-Teams/docs/rag-evaluation.md).

## Como desplegarlo en Azure

1. Copia [`.env.azure.example`](/c:/Users/maror/Projects/Personal/Asistente-Interno-Microsoft-Teams/.env.azure.example) a `.env.azure`.
2. Rellena secretos, nombre del proyecto y credenciales del bot.
3. Ejecuta:

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

Guia ampliada en [docs/deployment-azure.md](/c:/Users/maror/Projects/Personal/Asistente-Interno-Microsoft-Teams/docs/deployment-azure.md).

## Estrategia de costes

- desarrollar principalmente en local
- usar cloud para demo, validacion final y Teams
- parar PostgreSQL Flexible Server despues de la demo
- mantener SKUs pequenos
- no activar Azure OpenAI ni extras enterprise en esta fase

Detalle en [docs/cost-control.md](/c:/Users/maror/Projects/Personal/Asistente-Interno-Microsoft-Teams/docs/cost-control.md).

## Limitaciones reales del MVP

- no hay SSO ni RBAC real
- no hay Key Vault obligatorio
- no hay reranking avanzado
- la calidad RAG depende del corpus sintetico y del provider de embeddings
- Teams requiere tenant con custom apps o sideloading habilitado
- el flujo prioriza claridad tecnica y demo por encima de hardening enterprise

## Proximos pasos posibles

- endurecer evaluacion adversarial y prompt safety
- introducir seguridad por departamentos
- migrar secretos a Key Vault
- ampliar dataset y cobertura funcional
- evaluar Azure OpenAI o un provider enterprise equivalente
- mejorar el flujo Teams con cards mas ricas y telemetria adicional

## Estructura del repositorio

```text
internal-assistant-mvp/
+-- app-service/
+-- functions/
+-- src/internal_assistant/
+-- evaluation/
+-- docs/
+-- scripts/
+-- teams-app/
+-- infra/
+-- data/
`-- tests/
```

## Documentacion clave

- [docs/portfolio-summary.md](/c:/Users/maror/Projects/Personal/Asistente-Interno-Microsoft-Teams/docs/portfolio-summary.md)
- [docs/tradeoffs-and-decisions.md](/c:/Users/maror/Projects/Personal/Asistente-Interno-Microsoft-Teams/docs/tradeoffs-and-decisions.md)
- [docs/demo-script.md](/c:/Users/maror/Projects/Personal/Asistente-Interno-Microsoft-Teams/docs/demo-script.md)
- [docs/demo-checklist.md](/c:/Users/maror/Projects/Personal/Asistente-Interno-Microsoft-Teams/docs/demo-checklist.md)
- [docs/faq.md](/c:/Users/maror/Projects/Personal/Asistente-Interno-Microsoft-Teams/docs/faq.md)
- [docs/project-card.md](/c:/Users/maror/Projects/Personal/Asistente-Interno-Microsoft-Teams/docs/project-card.md)

## Licencia / aviso de uso

Proyecto orientado a portfolio tecnico y demo. Todo el dataset es ficticio y se incluye con fines demostrativos. Antes de publicar o reutilizar el codigo en un entorno real conviene revisar seguridad, gobierno de secretos, observabilidad y limites de coste.
