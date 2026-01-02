# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Antony Henry Oduor Onyango

"""
OMNIAI Core Application Entry Point

This is the heart of the system. It will evolve through Phase 1 as follows:

✅ [DONE] 1. Basic FastAPI app + health route + tenant middleware

🔜 [PHASE 1: Backend Engineering]
   - Add structured exception handlers (global error formatting)
   - Add CORS configuration (from security domain)
   - Register all API routers (users, orgs, audit, etc.)

🔜 [PHASE 1: Database Engineering]
   - Integrate SQLAlchemy engine and sessionmaker
   - Add startup/shutdown events:
       • Connect to DB on startup
       • Close pools on shutdown

🔜 [PHASE 1: Observability]
   - Attach OpenTelemetry or custom metrics exporter
   - Initialize logging configuration (structured, JSON)

🔜 [PHASE 1: Security]
   - Add security middleware chain:
       • Rate limiting
       • Request validation
       • JWT authentication (when auth service exists)
   - Enforce HTTPS in production (via middleware or proxy)

🔜 [PHASE 1: System Architecture]
   - Add async task queue initialization (Celery or asyncio)
   - Configure dependency injection container (if used)

🔜 [PHASE 1: Cloud & DevOps]
   - Add config loading from env + secrets manager
   - Support multiple environments (dev, staging, prod)

🔜 [PHASE 1: Engineering Mindset]
   - Add graceful shutdown handling (signal listeners)
   - Add startup diagnostics (log version, config hash)

🔜 [PHASE 2+]
   - Mount AI-specific routers (agents, RAG, etc.)
   - Add model monitoring hooks

IMPORTANT: This file should remain CLEAN.
- No business logic
- No DB queries
- Only wiring: middlewares, routers, lifecycle events
"""


# src/omniai/main.py
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.exc import OperationalError

from omniai.api.v1 import auth, me
from omniai.api.v1.agriculture import router as agriculture_router
from omniai.api.v1.health import router as health_router
from omniai.core.config import settings
from omniai.core.logging import logger
from omniai.core.logging_middleware import LoggingMiddleware
from omniai.core.middleware import TenantValidationMiddleware
from omniai.db.session import engine
from omniai.models.organization import Base as OrgBase
from omniai.models.user import Base as UserBase

# 🔒 Security & config audit at startup
logger.info(
    "application_startup_init",
    version="1.0",
    database_engine="postgresql",
    async_driver="asyncpg",
    token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    jwt_algorithm=settings.JWT_ALGORITHM,
    debug_mode=(len(settings.JWT_SECRET_KEY) < 32)  # Warn if key is too short!
)

if len(settings.JWT_SECRET_KEY) < 32:
    logger.critical(
        "security_risk_weak_jwt_secret",
        message="JWT_SECRET_KEY is less than 32 bytes — rotate immediately!"
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Wait for DB to be ready
    for i in range(10):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(UserBase.metadata.create_all)
                await conn.run_sync(OrgBase.metadata.create_all)
            logger.info("database_initialized", tables_created=["users", "organizations", "user_organization"])
            break
        except OperationalError as e:
            logger.warning("database_connection_retry", attempt=i+1, max_attempts=10, error=str(e))
            await asyncio.sleep(2)
    else:
        logger.error("database_connection_failed", message="Failed to connect to database after 10 attempts")
        raise RuntimeError("Failed to connect to database after 10 attempts")

    yield
    await engine.dispose()
    logger.info("application_shutdown", message="Database engine disposed")

app = FastAPI(
    title="OMNIAI Core Platform",
    description="The sovereign foundation for trillion-dollar AI applications.",
    version="0.1.0",
    lifespan=lifespan,
)

# Middleware (order matters!)
app.add_middleware(LoggingMiddleware)
app.add_middleware(TenantValidationMiddleware)

# Routers
app.include_router(health_router, prefix="/v1")
app.include_router(agriculture_router, prefix="/v1")
app.include_router(auth.router, prefix="/v1/auth")
app.include_router(me.router, prefix="/v1")

logger.info("application_startup_complete", message="OMNIAI Core is ready to accept requests")

def main():
    import uvicorn
    # ⚠️ Disable reload in production! (Only for dev)
    uvicorn.run("omniai.main:app", host="0.0.0.0", port=8000, reload=False)
