# Arquitectura

## Componentes

- `app-service`: FastAPI principal. Expone `/api/chat`, `/api/messages`, health checks, tickets, documentos y feedback.
- `custom-incidents-api-function`: sistema fuente simulado para incidencias.
- `indexer-function`: genera chunks, embeddings y mantiene el indice.
- `src/internal_assistant`: libreria compartida con configuracion, dominio, RAG, seguridad, cards y utilidades cloud/Teams.
- `PostgreSQL + pgvector`: persistencia principal.
- `teams-app`: manifiesto y empaquetado de la custom app.
- `infra`: Bicep modular para Azure.

## Flujo principal

1. El usuario pregunta desde `/api/chat` o desde Teams.
2. `app-service` detecta el intent.
3. Se generan embeddings y retrieval hibrido.
4. El provider LLM responde solo con evidencia recuperada.
5. Si falta evidencia, el sistema pide aclaracion.
6. Si sigue faltando evidencia, propone registrar incidencia.

## Registro de incidencia

1. El bot recopila campos minimos.
2. `app-service` llama a `custom-incidents-api-function`.
3. La Function crea el ticket en PostgreSQL.
4. `app-service` dispara `indexer-function`.
5. El ticket se chunkifica e indexa.

## Runtime y configuracion

- `config.py` centraliza App Settings para local y cloud.
- `runtime.py` valida configuracion por entorno y construye health checks avanzados.
- `teams.py` centraliza transformaciones de payloads de tarjetas y renderizado del manifiesto.

## Azure

- Web App Linux Python 3.12 para `app-service`
- Dos Function Apps Linux Consumption
- Storage Account comun para Functions
- PostgreSQL Flexible Server con allowlist de `vector`
- Application Insights opcional
- Azure Bot con canal Teams

## Observabilidad

- Logs JSON a stdout en local y cloud
- `retrieval_logs` en PostgreSQL
- Integracion opcional con Application Insights cuando existe `APPLICATIONINSIGHTS_CONNECTION_STRING`
