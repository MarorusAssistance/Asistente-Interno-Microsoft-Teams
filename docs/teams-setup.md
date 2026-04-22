# Teams setup

## Requisitos

- Tenant con sideloading o custom apps habilitado.
- Azure Bot desplegado.
- `MICROSOFT_APP_ID`, `MICROSOFT_APP_PASSWORD` y `MICROSOFT_APP_TENANT_ID`.
- `BOT_ENDPOINT` apuntando a `https://<webapp>.azurewebsites.net/api/messages`.

## Configurar el bot

1. Despliega la infraestructura con `./scripts/deploy_infra.sh`.
2. Verifica el recurso Azure Bot.
3. Comprueba que el endpoint del bot coincide con `/api/messages`.
4. Verifica que el canal Microsoft Teams esta habilitado.

## Generar el paquete Teams

```bash
./scripts/package_teams_app.sh
```

Salida:

- `teams-app/build/manifest.json`
- `teams-app/build/internal-assistant-demo.zip`

## Importar la app

1. Abre Teams.
2. Ve a Apps > Manage your apps > Upload a custom app.
3. Sube `internal-assistant-demo.zip`.
4. Agrega la app en `personal` o en un `team`.

## Pruebas recomendadas

- Mensaje personal al bot
- Mensaje en canal
- Pregunta con respuesta conocida
- Pregunta ambigua para forzar aclaraciones
- Feedback `no util`

## Problemas comunes

- `401` o `500` en `/api/messages`: revisar `MICROSOFT_APP_ID`, `MICROSOFT_APP_PASSWORD` y `MICROSOFT_APP_TENANT_ID`.
- La app no aparece en Teams: el tenant no permite custom apps o el zip es invalido.
- El bot no responde en canal: revisar el scope `team` en el manifiesto y el endpoint del bot.
- Las tarjetas no se ven: Teams usa fallback textual, pero revisa que el payload Adaptive Card sea valido.
