# omniai/db/session.py
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,  # ✅ Use async_sessionmaker (not sessionmaker)
)

from omniai.core.config import settings

# Production-grade async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,  # Recycle every 30 minutes
)

# ✅ Use async_sessionmaker — designed for AsyncSession
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for async DB sessions.
    Automatically closes session after request.
    """
    async with AsyncSessionLocal() as session:
        yield session