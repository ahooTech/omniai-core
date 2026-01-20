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

import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, Request
from sqlalchemy.exc import OperationalError
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse

from omniai.api.v1 import auth, me, health, agriculture
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
    debug_mode=(len(settings.JWT_SECRET_KEY) < 32)
)

if len(settings.JWT_SECRET_KEY) < 32:
    logger.critical(
        "security_risk_weak_jwt_secret",
        message="JWT_SECRET_KEY is less than 32 bytes — rotate immediately!"
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Initialize readiness flag
    app.state.ready = False

    # Wait for DB to be ready and create tables
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
        raise RuntimeError("Failed to connect to database after 10 attempts") from None

    # ✅ MARK AS READY AFTER STARTUP TASKS
    app.state.ready = True
    yield

    # Shutdown
    app.state.ready = False
    await engine.dispose()
    logger.info("application_shutdown", message="Database engine disposed")


app = FastAPI(
    title="OMNIAI Core Platform",
    description="The sovereign foundation for trillion-dollar AI applications.",
    version="0.1.0",
    lifespan=lifespan,
)


# Exception handler
async def rate_limit_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"error": "rate_limit_exceeded", "detail": exc.detail},
            headers=exc.headers or {},
        )
    return JSONResponse(status_code=500, content={"error": "server_error"})


app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Middleware (order matters!)
app.add_middleware(LoggingMiddleware)
app.add_middleware(TenantValidationMiddleware)

# Routers
app.include_router(health.router, prefix="/v1")
app.include_router(agriculture.router, prefix="/v1")
app.include_router(auth.router, prefix="/v1/auth")
app.include_router(me.router, prefix="/v1")

logger.info("application_startup_complete", message="OMNIAI Core is ready to accept requests")


if __name__ == "__main__":
    host = os.getenv("UVICORN_HOST", "127.0.0.1")
    port = int(os.getenv("UVICORN_PORT", "8000"))
    reload = os.getenv("UVICORN_RELOAD", "false").lower() == "true"

    uvicorn.run(
        "omniai.main:app",
        host=host,
        port=port,
        reload=reload,
    )