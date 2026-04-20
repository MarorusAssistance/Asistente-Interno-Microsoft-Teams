from __future__ import annotations

import httpx

from internal_assistant.config import get_settings


def main() -> None:
    settings = get_settings()
    headers = {"x-admin-api-key": settings.admin_api_key}
    response = httpx.post(f"{settings.indexer_api_base_url}/index/rebuild", headers=headers, timeout=120)
    response.raise_for_status()
    print(response.json())


if __name__ == "__main__":
    main()
