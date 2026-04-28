# Architecture diagram placeholder

## Nodos minimos del diagrama

- Usuario
- Microsoft Teams
- Azure Bot / `/api/messages`
- App Service `app-service`
- Custom Incidents API Function
- Indexer Function
- PostgreSQL + pgvector
- OpenAI o provider local compatible

## Flujos que conviene mostrar

1. Pregunta del usuario -> Teams o `/api/chat` -> App Service
2. App Service -> embeddings + retrieval -> PostgreSQL
3. App Service -> modelo -> respuesta con fuentes
4. Registro de incidencia -> Custom Incidents API -> PostgreSQL
5. Reindexado -> Indexer Function -> chunks + embeddings
6. Evaluacion RAG -> runners -> reportes JSON/Markdown

## Agrupacion visual sugerida

- azul: experiencia de usuario
- verde: servicios de aplicacion
- naranja: sistema fuente e indexado
- gris: persistencia
- morado o rojo suave: provider LLM

## Version minima valida para portfolio

Una version simple con cajas y flechas es suficiente si deja clara la separacion entre:

- fuente de verdad
- indice RAG
- orquestacion conversacional
- evaluacion
