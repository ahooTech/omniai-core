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

from contextlib import asynccontextmanager
from fastapi import FastAPI
from omniai.api.v1 import auth, me 
from omniai.api.v1.health import router as health_router
from omniai.api.v1.agriculture import router as agriculture_router
from omniai.core.middleware import TenantValidationMiddleware
from omniai.core.config import settings  # Reserved for future use

from omniai.models.user import Base as UserBase
from omniai.models.organization import Base as OrgBase
from omniai.db.session import engine


# Create DB Tables on Startup
from omniai.models.user import Base as UserBase
from omniai.models.organization import Base as OrgBase
from omniai.db.session import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    async with engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.create_all)
        await conn.run_sync(OrgBase.metadata.create_all)
    yield  # App runs here
    # Shutdown logic (optional for now)
    await engine.dispose()  # Cleanly close DB connections

app = FastAPI(
    title="OMNIAI Core Platform",
    description="The sovereign foundation for trillion-dollar AI applications.",
    version="0.1.0",
    lifespan=lifespan,  # ← This replaces @app.on_event
)

# Middleware
app.add_middleware(TenantValidationMiddleware)

# Routers — versioned at mount point
app.include_router(health_router, prefix="/v1")
app.include_router(agriculture_router, prefix="/v1")
app.include_router(auth.router, prefix="/v1/auth")
app.include_router(me.router, prefix="/v1")  # ← This is correct

# Optional: CLI runner -> for starting and testing the app localy but in production we will use docker
def main():
    import uvicorn
    uvicorn.run("omniai.main:app", host="0.0.0.0", port=8000, reload=True)