# Demo script

## Preparacion previa

1. Arrancar PostgreSQL cloud:

```bash
./scripts/start_postgres_azure.sh
```

2. Validar salud:

```bash
./scripts/smoke_test_cloud.sh
```

3. Tener a mano:
- Teams con la custom app importada
- URL del App Service
- consulta SQL o pgAdmin para `retrieval_logs`

## Preguntas preparadas

1. `Como se registra una entrega parcial en ventana critica en LogiCore ERP?`
2. `Como solicito acceso temporal a SafeGate para personal externo?`
3. `Que pasos de onboarding debo completar en la primera semana?`
4. `Que hago si RutaNexo no sincroniza una ruta aprobada?`
5. `Que politica aplica al uso de credenciales compartidas?`
6. `Como se revisa un pedido bloqueado por validacion manual?`

## Flujo sugerido

1. Mostrar una pregunta conocida y la respuesta con fuentes.
2. Mostrar una segunda pregunta relacionada con incidencias resueltas.
3. Lanzar una pregunta ambigua:
   - `No puedo entrar`
4. Mostrar las 2 aclaraciones.
5. Forzar la propuesta de registrar incidencia no resuelta.
6. Completar el flujo:
   - `si`
   - `titulo: Acceso denegado en SafeGate`
   - `descripcion: El torno principal no abre`
   - `departamento: Seguridad`
   - `categoria: accesos`
   - `sistema: SafeGate`
   - `impacto: bloquea el acceso del turno de noche`
   - `esperado: deberia permitir el acceso`
   - `actual: muestra acceso denegado`
   - `si`
7. Mostrar confirmacion del ticket creado e indexado.
8. Enviar feedback `no util`.
9. Mostrar `retrieval_logs`.

## Cierre

1. Recordar que el sistema usa datos ficticios, pero arquitectura realista.
2. Explicar que el despliegue esta preparado para Azure + Teams.
3. Parar PostgreSQL para reducir coste:

```bash
./scripts/stop_postgres_azure.sh
```
