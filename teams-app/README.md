# Teams app

Este directorio contiene el material para generar una custom app de Teams para la demo cloud.

## Archivos

- `manifest.template.json`: plantilla base del manifiesto.
- `color.png` y `outline.png`: iconos incluidos en el paquete.
- `build/`: salida generada por `scripts/package_teams_app.sh`.

## Generacion

1. Configura `MICROSOFT_APP_ID`, `TEAMS_APP_ID` y `BOT_ENDPOINT`.
2. Ejecuta:

   ```bash
   ./scripts/package_teams_app.sh
   ```

3. El zip final queda en `teams-app/build/internal-assistant-demo.zip`.

## Importante

- La app requiere tenant con sideloading o custom apps habilitado.
- El `BOT_ENDPOINT` debe apuntar a `/api/messages` del App Service desplegado.
