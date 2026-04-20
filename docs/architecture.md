# Arquitectura

## Componentes

- `app-service`: FastAPI principal con endpoints para chat, Bot Framework, tickets, documentos, feedback y health.
- `custom-incidents-api-function`: sistema fuente simulado de incidencias. Es la unica pieza que escribe en `incidents`.
- `indexer-function`: toma documentos e incidencias, genera chunks, embeddings y el indice hibrido.
- `PostgreSQL + pgvector`: persistencia de dominio, chunks, conversaciones, feedback y logs.

## Flujo principal de preguntas

1. El usuario envia una pregunta.
2. `app-service` detecta el intent y consulta el indice.
3. Se hace retrieval hibrido con vector search + full-text search.
4. El LLM responde solo con evidencia recuperada.
5. Si no hay evidencia suficiente, el bot pide aclaracion hasta 2 veces.
6. Si sigue sin poder responder, propone registrar una incidencia.

## Flujo de registro de incidencia

1. El usuario expresa que quiere registrar una incidencia.
2. El bot recopila campos minimos y guarda un borrador en `conversations.state`.
3. Tras la confirmacion, `app-service` llama a `custom-incidents-api-function`.
4. La Function persiste la incidencia y devuelve el registro creado.
5. `app-service` llama a `indexer-function` para indexar ese ticket.
6. El bot confirma al usuario que la incidencia fue creada e indexada.

## Modulos compartidos

- `config`: configuracion central con Pydantic Settings.
- `db`: engine, sesiones y base declarativa.
- `models`: tablas SQLAlchemy.
- `schemas`: contratos Pydantic.
- `rag`: chunking, scoring y retrieval.
- `llm`: interfaz de provider, OpenAI, Azure OpenAI preparado y mock.
- `chat`: orquestacion, intents y flujo conversacional.
- `cards`: payloads sencillos de Adaptive Cards con fallback textual.
- `observability`: logs estructurados y helpers de metricas.
- `security`: validacion de secretos compartidos y API keys.
