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

from fastapi import FastAPI
from omniai.api.v1.health import router as health_router
from omniai.api.v1.agriculture import router as agriculture_router
from omniai.core.middleware import TenantValidationMiddleware

app = FastAPI(
    title="OMNIAI Core Platform",
    description="The sovereign foundation for trillion-dollar AI applications.",
    version="0.1.0",
)

# Register middleware early in stack
app.add_middleware(TenantValidationMiddleware)

# Register routes AFTER middleware
# Exclude later because it is for ops and not user interaction. We will edit middleware.py to bypass checking health_router because we dont need middleware validation of tenant in order to check if system is alive
app.include_router(health_router) # All middlewares run first so we don't want an error in the middleware to block this code from running when being checked by aws, kubernetes e.t.c
app.include_router(agriculture_router)