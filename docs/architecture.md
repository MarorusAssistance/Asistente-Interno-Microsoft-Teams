# Arquitectura

## Objetivo arquitectonico

El proyecto modela un asistente interno con una idea central: la fuente de verdad y el indice RAG no son la misma cosa. Los tickets y documentos viven en PostgreSQL como datos operativos; el indice usa chunks, embeddings y full-text search para responder preguntas con latencia y relevancia razonables.

## Componentes

- `app-service`
  - FastAPI principal
  - expone `/api/chat`, `/api/messages`, health checks, feedback y endpoints de consulta
  - orquesta el flujo conversacional, el retrieval y la creacion de incidencias
- `custom-incidents-api-function`
  - sistema fuente simulado para incidencias
  - representa la capa donde se crean y actualizan tickets
- `indexer-function`
  - genera chunks, embeddings y actualiza el indice
  - reutiliza la misma logica que los scripts locales de reindexado
- `src/internal_assistant`
  - libreria compartida con configuracion, providers LLM, RAG, runtime, cards y repositorios
- `PostgreSQL + pgvector`
  - guarda incidents, documents, chunks, conversations, messages, feedback y retrieval logs
- `evaluation/`
  - datasets, metrics, judges y runners para evaluar retrieval y calidad de respuesta

## Flujo principal de pregunta y respuesta

1. El usuario pregunta desde `/api/chat` o desde Teams.
2. `app-service` clasifica el intent y genera embeddings de consulta.
3. `HybridRetriever` combina vector search y full-text search.
4. El provider LLM recibe solo el contexto recuperado.
5. El asistente responde con fuentes o pide aclaracion.
6. Si no hay evidencia suficiente tras dos aclaraciones, ofrece registrar incidencia.

## Flujo de registro de incidencia

1. El usuario acepta registrar un caso.
2. `app-service` recopila los campos minimos.
3. La incidencia se envia a `custom-incidents-api-function`.
4. La fuente simula la creacion del ticket y lo persiste.
5. `app-service` llama a `indexer-function`.
6. El indice se actualiza para que el caso pueda aparecer en retrieval posterior.

## Separacion entre fuente e indice

Esta separacion es una decision importante del proyecto:

- `incidents` y `documents` representan conocimiento operativo persistente
- `chunks` representa una vista derivada para retrieval

La demo muestra asi un patron mas realista que un simple bot que solo consulta un vector store sin distincion entre origen e indice.

## Runtime local y runtime cloud

### Local

- PostgreSQL en Docker o instalado en host
- FastAPI y Functions ejecutables con `uv run uvicorn`
- provider `mock`, `openai` o `openai_compatible`

### Cloud

- Azure App Service para `app-service`
- dos Azure Functions para incidents e indexer
- PostgreSQL Flexible Server con `pgvector`
- Azure Bot y Teams custom app para la ruta conversacional corporativa

## Observabilidad y evaluacion

- logs JSON a stdout
- `retrieval_logs` en PostgreSQL
- health checks simples y profundos
- framework de evaluacion RAG con reportes JSON y Markdown

La observabilidad es basica, pero suficiente para mostrar que el sistema no solo responde, sino que tambien puede medirse y depurarse.
