# Teams setup

## Requisitos

- tenant con custom apps o sideloading habilitado
- Azure Bot desplegado
- `MICROSOFT_APP_ID`, `MICROSOFT_APP_PASSWORD` y `MICROSOFT_APP_TENANT_ID`
- `BOT_ENDPOINT` apuntando a `https://<webapp>.azurewebsites.net/api/messages`

## Idea clave

El recurso Azure Bot por si solo no sustituye a la app de Teams. Para una prueba fiable necesitas:

1. bot desplegado y accesible
2. paquete de Teams generado
3. custom app subida al tenant

## Generar el paquete

```bash
./scripts/package_teams_app.sh
```

Salida esperada:

- `teams-app/build/manifest.json`
- `teams-app/build/internal-assistant-demo.zip`

## Subir la app

1. Abre Teams.
2. Ve a `Apps > Manage your apps`.
3. Usa `Upload a custom app`.
4. Sube `internal-assistant-demo.zip`.
5. Para la primera prueba, usa el scope `personal`.

## Pruebas recomendadas

- una pregunta con respuesta conocida
- una pregunta ambigua
- un caso de ticket no resuelto
- un feedback `no util`

## Problemas comunes

- `401` o `500` en `/api/messages`
  - revisar `MICROSOFT_APP_ID`, `MICROSOFT_APP_PASSWORD` y `MICROSOFT_APP_TENANT_ID`
- Teams abre pero no aparece el chat del bot
  - normalmente la app no esta instalada o la politica del tenant bloquea custom apps
- la app no aparece
  - zip invalido o sideloading deshabilitado
- las cards no se ven bien
  - el fallback textual debe seguir siendo entendible; revisa manifiesto y payload Adaptive Card
