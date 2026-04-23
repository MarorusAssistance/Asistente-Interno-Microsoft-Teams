# Evaluacion RAG

## Objetivo

La evaluacion RAG permite medir si el asistente:

- recupera las fuentes correctas;
- responde con informacion sustentada;
- cita fuentes validas;
- se abstiene cuando no hay evidencia;
- resiste casos ambiguos o maliciosos.

## Metricas

Retrieval:

- `hit_at_1`
- `hit_at_3`
- `hit_at_5`
- `recall_at_5`
- `mrr`
- `expected_source_coverage`
- `source_type_match_rate`

Respuesta:

- `answer_generated`
- `answer_contains_required_terms`
- `answer_avoids_forbidden_terms`
- `answer_mentions_uncertainty_when_needed`
- `answer_uses_only_retrieved_context`
- `answer_expected_behavior_match`

Fuentes:

- `citation_present_rate`
- `citation_source_validity_rate`
- `citation_coverage_rate`
- `unsupported_answer_rate`

Abstencion:

- `abstention_precision`
- `abstention_recall`
- `false_answer_when_should_abstain`
- `unnecessary_abstention_when_answer_exists`
- `clarification_rate_when_required`
- `incident_registration_offer_rate`

## Ejecucion local

Con mock:

```bash
python scripts/run_rag_eval.py --provider mock
```

Con OpenAI y casos adversariales:

```bash
python scripts/run_rag_eval.py --provider openai --include-adversarial
```

Comparacion de configuraciones de retrieval:

```bash
python scripts/compare_retrieval_configs.py
```

## Interpretacion

- Si `hit_at_5` es bajo, el problema principal esta en retrieval.
- Si `hit_at_5` es razonable pero `citation_coverage_rate` es baja, el asistente encuentra contexto pero no lo cita bien.
- Si `false_answer_when_should_abstain` sube, el sistema esta inventando demasiado.
- Si `clarification_rate_when_required` baja, el flujo ambiguo esta siendo demasiado agresivo.

## LLM-as-a-judge

`HeuristicJudge` es el default y no usa APIs externas. `LLMJudge` solo debe activarse cuando quieras una segunda señal semantica:

```bash
python scripts/run_rag_eval.py --provider openai --use-llm-judge
```

Para evitar gasto innecesario:

- usa `--provider mock` en CI;
- activa `--use-llm-judge` solo en evaluaciones manuales;
- revisa primero retrieval y metricas heuristicas antes de gastar tokens.

## Como ampliar el dataset

1. Añade una pregunta en `evaluation/datasets/rag_eval_questions.json`.
2. Usa `expected_source_ids` con la forma `document:<id>` o `incident:<id>`.
3. Si el caso requiere varios turnos, usa `follow_up_messages`.
4. Si es adversarial, añádelo a `evaluation/datasets/adversarial_questions.json`.

## Limitaciones

- Las metricas heuristicas no sustituyen una revision humana.
- `MockProvider` sirve para validar pipeline, no para medir calidad semantica real.
- En esta version no hay reranking avanzado ni LLM local generando datasets.
