from __future__ import annotations

from fastapi import Header, HTTPException, status

from internal_assistant.config import get_settings


def verify_admin_api_key(x_admin_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if x_admin_api_key != settings.admin_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ADMIN_API_KEY invalida")


def verify_shared_secret(x_app_shared_secret: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if x_app_shared_secret != settings.app_shared_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="APP_SHARED_SECRET invalido")
