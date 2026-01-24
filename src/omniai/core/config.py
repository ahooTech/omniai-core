# src/omniai/core/config.py
from typing import Any
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://user:password@localhost/omniai",
        description="Async PostgreSQL connection URL"
    )
    JWT_SECRET_KEY: str = Field(
        ...,  # required — must come from env
        description="Secret key for JWT signing — MUST be set in production"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        # Optional: add prefix like OMNIAI_
        # env_prefix="OMNIAI_",
    )

    def __init__(self, **kwargs: Any) -> None:
         # Allow empty init — Pydantic loads from env
        super().__init__(**kwargs)


@lru_cache()
def get_settings() -> Settings:
    return Settings()