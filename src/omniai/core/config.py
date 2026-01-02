# src/omniai/core/config.py
# multi database multi country
from typing import Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, ValidationError

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


# ❗ Critical: Validate at startup
try:
    settings = Settings()
    # set DATABASE_URL=postgresql://prod/proddb
    # python -c "from omniai.core.config import settings; print(settings.DATABASE_URL)"
except ValidationError as e:
    print("❌ Missing required environment variables:")
    for error in e.errors():
        print(f"  - {error['loc'][0]}: {error['msg']}")
    raise SystemExit(1)