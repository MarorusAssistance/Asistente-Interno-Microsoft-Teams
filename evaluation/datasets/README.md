# Datasets de evaluacion

Archivos incluidos:

- `rag_eval_questions.json`: escenarios principales de retrieval y respuesta.
- `adversarial_questions.json`: intentos de prompt injection, peticiones de secretos, casos fuera de ambito y preguntas ambiguas.

Contrato por pregunta:

- `id`
- `question`
- `category`
- `expected_behavior`
- `expected_source_types`
- `expected_source_ids`
- `expected_answer_summary`
- `must_include_terms`
- `must_not_include_terms`
- `requires_clarification`
- `should_create_incident`
- `follow_up_messages`

Convencion de fuentes esperadas:

- `document:<id>`
- `incident:<id>`

Los datasets son estaticos y estan curados contra el seed actual del repo. No se generan en runtime.
