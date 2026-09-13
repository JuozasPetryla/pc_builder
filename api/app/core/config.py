from functools import lru_cache

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PC Builder API"
    app_env: str = "development"
    database_url: PostgresDsn = PostgresDsn(
        "postgresql+psycopg://pc_builder:change-me@localhost:5432/pc_builder"
    )
    cors_origins: list[str] = ["http://localhost:8080", "http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
