# Control de costes

## Principios del MVP

- Embeddings de 512 dimensiones con `text-embedding-3-small`.
- Top 5 global tras retrieval hibrido, sin reranking avanzado.
- Dataset seed local y funciones desacopladas para apagar o escalar por separado.
- Logging util pero acotado: se guardan ids y scores, no el texto completo de todos los chunks.

## Recomendaciones

- Cachear consultas frecuentes en una fase siguiente.
- Limitar reconstrucciones completas del indice y priorizar indexado incremental.
- Ajustar el umbral de confianza para reducir llamadas innecesarias al LLM.
- Migrar a Azure OpenAI cuando se quiera consolidar control de red, compliance y tenancy.
