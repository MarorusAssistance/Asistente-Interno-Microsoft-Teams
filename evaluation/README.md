# Evaluacion RAG

Este directorio contiene el framework de evaluacion del asistente:

- `datasets/`: preguntas principales y adversariales.
- `metrics/`: metricas de retrieval, respuesta, citas y abstencion.
- `judges/`: juez heuristico por defecto, juez mock para tests y juez LLM opcional.
- `runners/`: ejecucion de retrieval eval, answer eval, ablation y full eval.
- `reports/`: salida JSON y Markdown con timestamp.

Flujos habituales:

```bash
python scripts/run_rag_eval.py --provider mock
python scripts/run_rag_eval.py --provider openai --include-adversarial
python scripts/compare_retrieval_configs.py
```

Notas:

- `MockProvider` sirve para smoke tests y CI sin llamadas externas.
- `LLMJudge` es opcional y solo debe activarse cuando quieras una señal semantica adicional.
- Los datasets usan IDs compuestos `document:<id>` e `incident:<id>` para alinear fuentes esperadas con la base real.
