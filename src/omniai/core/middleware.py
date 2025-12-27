"""
OMNIAI Core Middleware Layer

This file will evolve through Phase 1 as follows:

✅ [DONE] 1. TenantValidationMiddleware
   - Control flow mastery: distinguish missing vs invalid tenant ID
   - Early-return guard clauses
   - Structured error responses

🔜 [PHASE 1: Security & Hardening]
   - Add CORS middleware with secure defaults
   - Add CSRF protection (for cookie-based auth later)
   - Add security headers (HSTS, CSP, X-Content-Type-Options)
   - Integrate with RBAC system (inject user roles from JWT)

🔜 [PHASE 1: Backend Engineering]
   - Add LoggingMiddleware: structured logs with trace_id, tenant_id, duration
   - Add RequestIDMiddleware: inject X-Request-ID for distributed tracing

🔜 [PHASE 1: Observability]
   - Add MetricsMiddleware: increment Prometheus counters (requests, errors)
   - Add SLO monitoring hooks (e.g., log if latency > 1s)

🔜 [PHASE 1: Backend Engineering + Security]
   - Add RateLimitingMiddleware:
       • Token bucket algorithm
       • Redis-backed counters
       • Per-tenant and per-endpoint limits
       • Retry-After header on 429

🔜 [PHASE 1: System Architecture]
   - Add CorrelationID propagation (for microservices future)
   - Add TenantContextMiddleware (attach full tenant object from DB after models exist)

🔜 [PHASE 1: Engineering Mindset]
   - Add comprehensive middleware test suite:
       • Unit tests for all edge cases
       • Integration tests with real auth flow
   - Add middleware ordering documentation (order matters!)

🔜 [PHASE 2+ Integration]
   - Add AI-specific middleware:
       • Token usage tracking
       • Prompt injection detection
       • Model routing headers

NOTE: Only implement features when their prerequisite skills are mastered.
Do not pre-optimize. Build incrementally.
"""

# src/omniai/core/middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException
from starlette.responses import JSONResponse
from jose import jwt, JWTError
from omniai.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from omniai.db.session import AsyncSessionLocal
from omniai.models.user import user_organization

# Public paths (no auth needed)
PUBLIC_PATHS = {
    "/v1/health",
    "/metrics",
    "/ready",
    "/v1/auth/signup",
    "/v1/auth/login",
    "/docs",
    "/openapi.json",
}

class TenantValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # === STEP 1: Authenticate user via JWT ===
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": {"code": "MISSING_AUTH_TOKEN", "message": "Authorization header missing"}}
            )

        token = auth_header[7:]
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                options={
                    "verify_exp": True,      # Always verify expiration (default, but explicit)
                    "require": ["exp", "sub"]  # Enforce presence of critical claims
                }
            )
            user_id = payload.get("sub")  # ← MUST be user.id, not email!
            if not isinstance(user_id, str) or not user_id.startswith("usr_"):
                raise JWTError("Invalid user ID format")
            
        except JWTError:
            return JSONResponse(
                status_code=401,
                content={"error": {"code": "INVALID_TOKEN", "message": "Invalid or expired token"}}
            )

        # === STEP 2: Get tenant from X-Tenant-ID header ===
        tenant_id = request.headers.get("x-tenant-id")
        if not tenant_id:
            # If missing, use user's DEFAULT org
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(user_organization.c.organization_id)
                    .where(
                        user_organization.c.user_id == user_id,
                        user_organization.c.is_default == True
                    )
                )
                default_org = result.scalar_one_or_none()
                if not default_org:
                    return JSONResponse(
                        status_code=403,
                        content={"error": {"code": "NO_DEFAULT_ORG", "message": "User has no default organization"}}
                    )
                tenant_id = default_org

        # === STEP 3: Validate user is member of tenant_id ===
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(user_organization.c.organization_id)
                .where(
                    user_organization.c.user_id == user_id,
                    user_organization.c.organization_id == tenant_id
                )
            )
            if result.scalar_one_or_none() is None:
                return JSONResponse(
                    status_code=403,
                    content={"error": {"code": "NOT_ORG_MEMBER", "message": "Not a member of the specified organization"}}
                )

        # === STEP 4: Attach to request ===
        request.state.user_id = user_id
        request.state.tenant_id = tenant_id

        return await call_next(request)