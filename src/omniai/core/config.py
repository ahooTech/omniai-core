# multi database multi country
# security via JWT for each organizations .env
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/omniai"
    JWT_SECRET_KEY: str = "supersecret"  # Replace in production!
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
# set DATABASE_URL=postgresql://prod/proddb
# python -c "from omniai.core.config import settings; print(settings.DATABASE_URL)"