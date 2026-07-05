from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Live Stream Clip Agent"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/live-stream-clip-agent"
    redis_url: str = "redis://localhost:6379/0"
    storage_dir: str = "data/files"
    api_key: str = "dev-live-stream-clip-agent"
    frontend_origin: str = "http://localhost:5173"
    frontend_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str = "gpt-4.1-mini"
    llm_mock: bool = Field(default=True)
    langsmith_tracing: bool = False

    @property
    def cors_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]
        if self.frontend_origin.strip():
            origins.append(self.frontend_origin.strip())
        return list(dict.fromkeys(origins))


@lru_cache
def get_settings() -> Settings:
    return Settings()
