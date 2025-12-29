
# tests/conftest.py
import os
from pathlib import Path
from dotenv import load_dotenv
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import text
from omniai.core.config import Settings
from omniai.models.user import Base as UserBase
from omniai.models.organization import Base as OrgBase

# --- Load test environment ---
env_path = Path(__file__).parent.parent.parent / ".env.test.docker"
if env_path.exists():
    load_dotenv(env_path, override=True)
else:
    raise RuntimeError(f"The test env file does not exist at: {env_path.absolute()}")


# Manually create settings using .env.test
test_settings = Settings(_env_file=env_path) 

# --- Safety check: only allow test DB ---
if "omniai_test" not in test_settings.DATABASE_URL:
    raise RuntimeError("Refusing to run tests: DATABASE_URL must contain 'omniai_test', got: {test_settings.DATABASE_URL}")

# --- Async test engine (session-scoped) ---
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session")
async def test_engine():
    # Use NullPool to avoid connection conflicts in tests
    engine = create_async_engine(
        test_settings.DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )
    # Create all tables (exactly like your lifespan)
    async with engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.create_all)
        await conn.run_sync(OrgBase.metadata.create_all)
        # Ensure UUID extension is available (if you use UUIDs)
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
    yield engine
    await engine.dispose()

# --- Per-test transaction rollback (no cleanup needed) ---
@pytest.fixture
async def test_db(test_engine):
    async with test_engine.connect() as conn:
        # Begin outer transaction
        trans = await conn.begin()
        # Begin nested transaction (savepoint)
        await conn.begin_nested()

        # Create session bound to this connection
        async with AsyncSession(bind=conn) as session:
            yield session

        # Rollback outer transaction → undo all changes
        await trans.rollback()
