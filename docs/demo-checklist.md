# Demo checklist

## Pre-demo

- PostgreSQL arrancado y accesible
- `/api/health` y `/api/health/deep` en verde
- incidents, documents y chunks presentes
- provider LLM revisado para el entorno elegido
- `OPENAI_API_KEY` disponible si aplica
- `LLM_BASE_URL` correcto si se usa provider local compatible
- custom incidents API accesible
- indexer accesible
- paquete Teams generado si se usa Teams
- preguntas de demo preparadas
- ultimo reporte de evaluacion localizado
- costes bajo control si la demo es cloud

## Durante la demo

- empezar por una pregunta resuelta con fuentes
- ensenar una aclaracion
- ensenar un caso no resuelto con registro de incidencia
- ensenar feedback `no util`
- ensenar un reporte de evaluacion RAG

## Post-demo

- revisar logs o `retrieval_logs` si hubo algun fallo
- parar PostgreSQL Azure si se uso cloud
- revisar si se han creado tickets demo que convenga limpiar
- guardar feedback cualitativo de la sesion
- comprobar que no se han dejado secretos visibles en terminal, capturas o bundles
