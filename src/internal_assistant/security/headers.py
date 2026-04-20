from __future__ import annotations

from internal_assistant.config import get_settings


def assert_shared_secret(value: str | None) -> bool:
    settings = get_settings()
    return value == settings.app_shared_secret


def assert_admin_api_key(value: str | None) -> bool:
    settings = get_settings()
    return value == settings.admin_api_key
