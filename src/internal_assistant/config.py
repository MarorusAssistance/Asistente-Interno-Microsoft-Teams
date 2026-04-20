from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="local", alias="APP_ENV")
    app_name: str = Field(default="internal-assistant-mvp", alias="APP_NAME")
    database_url: str = Field(
        default="postgresql+psycopg://assistant:assistant@localhost:5432/assistant",
        alias="DATABASE_URL",
    )
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    chat_model: str = Field(default="gpt-4o-mini", alias="CHAT_MODEL")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")
    embedding_dimensions: int = Field(default=512, alias="EMBEDDING_DIMENSIONS")
    admin_api_key: str = Field(default="change-this-admin-key", alias="ADMIN_API_KEY")
    app_shared_secret: str = Field(default="change-this-shared-secret", alias="APP_SHARED_SECRET")
    custom_incidents_api_base_url: str = Field(default="http://localhost:7071", alias="CUSTOM_INCIDENTS_API_BASE_URL")
    indexer_api_base_url: str = Field(default="http://localhost:7072", alias="INDEXER_API_BASE_URL")
    bot_app_id: str = Field(default="", alias="BOT_APP_ID")
    bot_app_password: str = Field(default="", alias="BOT_APP_PASSWORD")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    retrieval_confidence_threshold: float = Field(default=0.58, alias="RETRIEVAL_CONFIDENCE_THRESHOLD")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
