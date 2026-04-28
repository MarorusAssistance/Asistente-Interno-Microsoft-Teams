# FAQ

## Que diferencia hay entre tickets e indice RAG?

Los tickets son conocimiento operativo persistido como fuente de verdad. El indice RAG es una vista derivada optimizada para retrieval, formada por chunks y embeddings.

## Por que no usar Azure AI Search desde el principio?

Porque el objetivo del MVP era demostrar retrieval hibrido, trazabilidad y despliegue barato con el menor numero de piezas posible.

## Que parte corre en Azure y cual en local?

En local pueden correr PostgreSQL, FastAPI, las Functions y un provider LLM local. En cloud, la ruta preparada usa App Service, Azure Functions, PostgreSQL Flexible Server y Azure Bot.

## Esto esta preparado para produccion?

No. Esta preparado para demo tecnica y portfolio. Faltan capas de seguridad, identidad, gobierno de secretos y hardening operativo.

## Como se controlan costes?

Priorizando local para desarrollo, usando SKUs pequenos en Azure y parando PostgreSQL Flexible Server despues de la demo.

## Como se evitan respuestas inventadas?

Con retrieval previo, citas, umbral de confianza, aclaraciones y una salida controlada hacia registro de incidencia cuando no hay evidencia suficiente.

## Que pasa si no encuentra solucion?

Primero pide aclaracion. Si tras dos intentos sigue sin evidencia suficiente, propone registrar una incidencia no resuelta.

## Puede registrar conocimiento nuevo?

Si. Cuando se crea una incidencia nueva, se guarda en el sistema fuente simulado y luego se dispara el indexado para incorporarla al indice.

## Como se evalua la calidad del asistente?

Con un framework de evaluacion RAG que mide retrieval, calidad de respuesta, citas, abstencion y robustez adversarial.

## Se puede migrar a Azure OpenAI?

Si. El proyecto deja esa ruta preparada, pero no la hace obligatoria en la version actual.

## Se puede anadir seguridad por departamentos?

Si, pero no esta implementado todavia. La extension natural seria filtrar retrieval y permisos segun identidad y area funcional.
