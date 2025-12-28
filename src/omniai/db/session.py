# Mix-ups: Your data never gets tangled with someone else’s.
# Leaks: After your request is done, the connection is fully closed — no leftover access.
# Overload: The system handles many users at once without crashing (like a bank with enough tellers).
# Speed: It reuses safe connections efficiently so things feel fast.


# 🔁 The Pattern Is Always the Same:
# You do something (click, type, ask).
# OMNIAI opens a clean, private, short-lived connection to the database.
# It reads or writes only what’s needed — nothing extra.
# It closes the connection immediately — like hanging up a phone call.
# You get your result — fast, safe, and personal.
# 🛡️ Why This Matters to You (the user):
# No data leaks: Your info never gets “stuck” in a shared connection.
# No slowdowns: Even if 10,000 people use OMNIAI at once, each gets their own lane.
# No corruption: Two people saving data at the same time won’t overwrite each other.
# Total privacy: The system only sees your data when you’re actively using it.


# omniai/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from omniai.core.config import settings

# Production-grade async engine
# - pool_size=10: steady connections
# - max_overflow=20: burst capacity
# - echo=False: no SQL logging in prod
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    # Optional: add timeouts for resilience
    pool_timeout=30,
    pool_recycle=1800,  # Recycle connections every 30 min (avoid stale DB conns)
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    """
    FastAPI dependency for DB sessions.
    Automatically closes session after request.
    """
    async with AsyncSessionLocal() as session:
        yield session