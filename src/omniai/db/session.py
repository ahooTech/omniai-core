# omniai/db/session.py
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from omniai.core.config import get_settings  # ✅ Import the function

# ✅ Get settings ONCE at module load time
_settings = get_settings()

# Production-grade async engine
engine = create_async_engine(
    _settings.DATABASE_URL,  # ← Use local _settings
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session