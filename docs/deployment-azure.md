# Despliegue Azure

## Fase prevista

En una segunda fase el despliegue se llevara a Azure con:

- Azure App Service para `app-service`
- Azure Functions para `custom-incidents-api-function` e `indexer-function`
- Azure Database for PostgreSQL Flexible Server con pgvector
- Storage Account para Azure Functions
- Application Insights para observabilidad
- Bot Channels Registration para Teams
- Key Vault para secretos

## Estado actual

- La estructura del repo ya separa componentes de forma compatible con ese despliegue.
- `AzureOpenAIProvider` queda preparado para activarse cuando se decida migrar de proveedor.
- No se incluye Bicep real en esta version.
