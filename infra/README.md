# Infraestructura Azure

Este directorio contiene la infraestructura modular en Bicep para desplegar la demo cloud del MVP.

## Archivos

- `main.bicep`: orquesta recursos y wiring principal.
- `main.parameters.example.json`: ejemplo de parametros.
- `modules/app-service.bicep`: plan Linux y Web App FastAPI.
- `modules/functions.bicep`: plan Consumption Linux y las dos Function Apps.
- `modules/postgres.bicep`: PostgreSQL Flexible Server, base de datos y allowlist de `vector`.
- `modules/storage.bicep`: Storage Account para Functions.
- `modules/app-insights.bicep`: Application Insights workspace-based y Log Analytics.
- `modules/bot.bicep`: Azure Bot y canal de Teams.

## Uso

El flujo manual previsto es:

```bash
az login
./scripts/deploy_infra.sh
./scripts/configure_app_settings.sh
./scripts/deploy_app_service.sh
./scripts/deploy_functions.sh
```

## Notas

- El Resource Group no se crea en `main.bicep`; lo crea `scripts/deploy_infra.sh` si no existe.
- PostgreSQL queda configurado para permitir `vector`, pero la extension sigue creandose desde migraciones o scripts SQL del proyecto.
- No se incluye Key Vault en v0.2; los secretos se pasan por App Settings.
