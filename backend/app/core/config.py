from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str
    database_url: str
    redis_url: str
    storage_dir: str
    api_key: str
    frontend_origin: str
    frontend_origins: str
    llm_base_url: str | None
    llm_api_key: str | None
    llm_model: str
    llm_mock: bool
    langsmith_tracing: bool
    asr_provider: str
    asr_model: str
    asr_api_key: str | None
    asr_base_url: str
    asr_max_duration_sec: int
    asr_max_payload_bytes: int
    asr_segment_duration_sec: int
    asr_request_timeout_sec: int
    ffmpeg_path: str | None
    ffprobe_path: str | None

    @property
    def cors_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]
        if self.frontend_origin.strip():
            origins.append(self.frontend_origin.strip())
        return list(dict.fromkeys(origins))


@lru_cache
def get_settings() -> Settings:
    return Settings()
