# Control de costes

## Recursos que generan coste

- Azure App Service Plan Linux
- Azure Functions
- Azure Database for PostgreSQL Flexible Server
- Storage Account
- Application Insights / Log Analytics

## Estrategia recomendada para demo

1. Arrancar PostgreSQL:

```bash
./scripts/start_postgres_azure.sh
```

2. Validar health:

```bash
./scripts/smoke_test_cloud.sh
```

3. Hacer la demo.
4. Parar PostgreSQL:

```bash
./scripts/stop_postgres_azure.sh
```

## Comandos Azure CLI

```bash
az postgres flexible-server start --resource-group <rg> --name <server>
az postgres flexible-server stop --resource-group <rg> --name <server>
```

## Notas importantes

- Parar PostgreSQL reduce el coste de compute, pero storage y backups pueden seguir generando coste.
- Azure PostgreSQL Flexible Server puede permanecer parado hasta 7 dias; despues Azure puede reiniciarlo.
- Si quieres coste cero total, borra el Resource Group entero.
- No actives Azure OpenAI en v0.2; OpenAI API ya cubre la demo.
- Mantente en SKUs bajos:
  - App Service Plan `B1`
  - PostgreSQL `Standard_B1ms`
  - Storage `Standard_LRS`
  - Functions en Consumption

## Recomendaciones adicionales

- Crea budget alerts en Azure Cost Management.
- No uses alta disponibilidad ni private endpoints en esta fase.
- Reconstruye el indice solo cuando cambie el dataset o registres incidencias nuevas.
