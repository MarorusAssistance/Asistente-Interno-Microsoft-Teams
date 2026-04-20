# Demo script

## Objetivo

Mostrar un recorrido corto de extremo a extremo del asistente interno para una empresa ficticia de logistica.

## Pasos sugeridos

1. Abrir `POST /api/chat` con una pregunta de documentacion:
   - "Como se gestiona la entrega parcial en LogiCore ERP?"
2. Enseñar la respuesta con fuentes y fragmentos.
3. Lanzar una pregunta ambigua:
   - "No puedo entrar"
4. Mostrar la primera y la segunda aclaracion.
5. Mantener la ambiguedad para forzar la propuesta de registrar incidencia.
6. Registrar una incidencia no resuelta.
7. Mostrar la confirmacion del ticket creado e indexado.
8. Volver a consultar la incidencia recien creada desde `GET /api/tickets/{id}`.
9. Enviar feedback util/no util desde la API.
10. Enseñar los logs de recuperacion en base de datos.
