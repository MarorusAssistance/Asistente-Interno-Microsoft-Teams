# Tradeoffs and decisions

## PostgreSQL + pgvector en lugar de Azure AI Search Basic

**Contexto**  
El proyecto necesitaba retrieval hibrido, coste bajo, operacion local sencilla y una persistencia unica para el MVP.

**Decision tomada**  
Usar PostgreSQL + pgvector y full-text search nativo.

**Alternativa descartada**  
Azure AI Search desde la primera version.

**Impacto**  
La arquitectura es mas compacta y barata para portfolio. A cambio, se pierde parte de la experiencia gestionada y capacidades avanzadas de busqueda.

**Trabajo futuro posible**  
Evaluar Azure AI Search cuando el objetivo pase de demo a un servicio mas cercano a produccion.

## OpenAI primero y Azure OpenAI despues

**Contexto**  
El objetivo era tener un provider cloud funcional y facil de validar sin bloquear el MVP por requisitos extra de Azure.

**Decision tomada**  
Dejar OpenAI API como provider inicial y preparar `AzureOpenAIProvider` sin hacerlo obligatorio.

**Alternativa descartada**  
Forzar Azure OpenAI desde v0.1.

**Impacto**  
La puesta en marcha es mas simple y el proyecto sigue siendo Azure-ready. A cambio, no se demuestra la ruta corporativa completa de IA gestionada dentro de Azure.

**Trabajo futuro posible**  
Completar Azure OpenAI y exponer una comparativa de configuracion por entorno.

## Dataset estatico antes que generacion con LLM local

**Contexto**  
Para medir el sistema hacia falta un corpus controlado y reproducible.

**Decision tomada**  
Mantener `seed_tickets.json` y `seed_documents.json` como datasets estaticos curados.

**Alternativa descartada**  
Generar tickets y documentos sinteticos en runtime con un LLM local.

**Impacto**  
Las pruebas y la evaluacion son repetibles. A cambio, el corpus es menos variado y requiere mantenimiento manual.

**Trabajo futuro posible**  
Anadir tooling de generacion o ampliacion asistida del dataset, separado del flujo principal.

## Sin RBAC real en esta fase

**Contexto**  
La demo queria centrarse en retrieval, grounding y operativa conversacional, no en seguridad enterprise completa.

**Decision tomada**  
No introducir seguridad por departamentos ni permisos reales por usuario.

**Alternativa descartada**  
Implementar RBAC parcial o reglas por departamento desde el MVP.

**Impacto**  
La demo es mas simple de entender y ejecutar. A cambio, el proyecto no debe presentarse como listo para produccion en entornos regulados.

**Trabajo futuro posible**  
Aplicar claims de identidad y filtros de retrieval por area o sistema.

## Flujo de aclaraciones limitado a dos intentos

**Contexto**  
Un asistente que pide aclaraciones indefinidamente empeora la experiencia y complica la demo.

**Decision tomada**  
Pedir hasta dos aclaraciones antes de ofrecer registrar una incidencia.

**Alternativa descartada**  
Permitir cualquier numero de aclaraciones o responder siempre aunque falte contexto.

**Impacto**  
El flujo queda claro y demostrable. A cambio, algunos casos legitimos pueden cerrarse antes de tiempo.

**Trabajo futuro posible**  
Ajustar el limite por intent o por tipo de consulta.

## Evaluacion heuristica con judge LLM opcional

**Contexto**  
Hacia falta una forma reproducible y barata de medir calidad RAG sin depender siempre de llamadas externas.

**Decision tomada**  
Usar heuristicas por defecto y `LLMJudge` solo cuando se active explicitamente.

**Alternativa descartada**  
Basar toda la evaluacion en un juez LLM.

**Impacto**  
La suite puede ejecutarse en CI sin gastar tokens. A cambio, la senal semantica es menos rica en el modo por defecto.

**Trabajo futuro posible**  
Combinar heuristicas, muestreo manual y LLM judge en pipelines periodicos.

## Teams como custom app y no como AppSource

**Contexto**  
La prioridad era una demo controlada para portfolio y tenant propio.

**Decision tomada**  
Empaquetar la app como custom app de Teams.

**Alternativa descartada**  
Intentar un flujo de publicacion o distribucion tipo AppSource.

**Impacto**  
El tiempo de entrega baja y la instalacion es suficiente para demo. A cambio, el escenario multi-tenant y la distribucion publica quedan fuera.

**Trabajo futuro posible**  
Madurar compliance, branding y despliegue antes de pensar en publicacion externa.

## Priorizar portfolio sobre hardening enterprise

**Contexto**  
El proyecto debe ser entendible, demostrable y relativamente barato de operar.

**Decision tomada**  
Optimizar por claridad arquitectonica, scripts reproducibles y material de demo.

**Alternativa descartada**  
Introducir mas capas enterprise antes de cerrar la historia principal del producto.

**Impacto**  
La narrativa tecnica queda mucho mas limpia. A cambio, algunas decisiones no son las definitivas para produccion real.

**Trabajo futuro posible**  
Usar este MVP como base para una iteracion centrada en seguridad, gobernanza y operaciones.
