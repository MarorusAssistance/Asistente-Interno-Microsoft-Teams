# Project card

## Nombre

Internal Assistant MVP

## Resumen

Asistente interno con RAG para una empresa ficticia de logistica. Combina documentacion privada, incidencias historicas y registro de tickets nuevos en un flujo conversacional que prioriza respuestas con evidencia, aclaraciones cuando falta contexto y evaluacion reproducible de calidad RAG.

## Stack

- Python 3.12
- FastAPI
- Azure Functions
- PostgreSQL + pgvector
- SQLAlchemy + Alembic
- OpenAI / provider OpenAI-compatible
- Azure App Service, Azure Bot y Teams custom app

## Retos tecnicos

- separar sistema fuente e indice RAG
- implementar retrieval hibrido sin un buscador externo dedicado
- mantener trazabilidad de fuentes
- gestionar abstencion y aclaraciones sin inventar procedimientos
- medir calidad RAG con datasets y reportes reproducibles

## Decisiones importantes

- PostgreSQL + pgvector antes que Azure AI Search
- OpenAI primero y Azure OpenAI despues
- evaluacion heuristica por defecto con judge LLM opcional
- Teams como custom app para demo controlada

## Estado actual

MVP funcional en local, desplegable en Azure, con evaluacion RAG y ruta de demo en Teams.

## Que ensenaria en una demo

- una consulta resuelta con fuentes
- una consulta ambigua que fuerza aclaracion
- un caso no resuelto que termina en ticket nuevo
- un reporte de evaluacion RAG con retrieval y citation coverage
