# multi database multi country
# security via JWT for each organizations .env
# config.py
from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://user:password@localhost/omniai",
        description="Async PostgreSQL connection URL"
    )
    JWT_SECRET_KEY: str = Field(
        ...,  # ← NO DEFAULT — raises error if missing
        description="Secret key for JWT signing — MUST be set in production"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
# set DATABASE_URL=postgresql://prod/proddb
# python -c "from omniai.core.config import settings; print(settings.DATABASE_URL)"

