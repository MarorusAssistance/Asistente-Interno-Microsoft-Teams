# Evaluacion RAG

## Por que evaluar el RAG

El asistente no se da por valido solo porque responda. Hay que comprobar:

- si recupera las fuentes adecuadas
- si responde con el comportamiento esperado
- si cita bien
- si se abstiene cuando debe
- si resiste preguntas ambiguas o maliciosas

## Que metricas se usan

### Retrieval

- `hit_at_1`
- `hit_at_3`
- `hit_at_5`
- `recall_at_5`
- `mrr`
- `expected_source_coverage`
- `source_type_match_rate`

### Respuesta

- `answer_generated`
- `answer_contains_required_terms`
- `answer_avoids_forbidden_terms`
- `answer_mentions_uncertainty_when_needed`
- `answer_uses_only_retrieved_context`
- `answer_expected_behavior_match`

### Fuentes

- `citation_present_rate`
- `citation_source_validity_rate`
- `citation_coverage_rate`
- `unsupported_answer_rate`

### Abstencion

- `abstention_precision`
- `abstention_recall`
- `false_answer_when_should_abstain`
- `unnecessary_abstention_when_answer_exists`
- `clarification_rate_when_required`
- `incident_registration_offer_rate`

## Como ejecutar la evaluacion

### Smoke test barato

```bash
python -m uv run python scripts/run_rag_eval.py --provider mock
```

### OpenAI

```bash
python -m uv run python scripts/run_rag_eval.py --provider openai --include-adversarial
```

### Provider local compatible

```bash
python -m uv run python scripts/run_rag_eval.py --provider openai_compatible --include-adversarial
```

### Judge LLM opcional

```bash
python -m uv run python scripts/run_rag_eval.py --provider openai --use-llm-judge
```

### Ablation de retrieval

```bash
python -m uv run python scripts/compare_retrieval_configs.py
```

## Donde quedan los resultados

Los reportes se guardan en `evaluation/reports/` como archivos JSON y Markdown. No se suben automaticamente a PostgreSQL, Table Storage, Blob Storage ni a artifacts remotos.

## Como interpretar los reportes

- `hit_at_5` bajo suele indicar un problema primario de retrieval
- `citation_coverage_rate` baja indica que la respuesta no esta usando o exponiendo bien las fuentes correctas
- `false_answer_when_should_abstain` alto significa que el asistente esta inventando demasiado
- `clarification_rate_when_required` bajo indica que el flujo ambiguo esta siendo demasiado agresivo

## LLM-as-a-judge

`HeuristicJudge` es el modo por defecto y no usa APIs externas. `LLMJudge` es una segunda senal semantica util para evaluaciones manuales, pero no deberia ser obligatorio en CI.

## Como evitar gastar tokens

- usa `mock` para smoke tests
- activa `LLMJudge` solo en evaluaciones manuales
- en provider local compatible, ajusta timeout y concurrencia con cuidado

## Limitaciones

- las metricas heuristicas no sustituyen una revision humana
- `MockProvider` valida el pipeline, pero no mide calidad semantica real
- un benchmark solo es comparable si el provider de consulta y el indice comparten el mismo espacio de embeddings
