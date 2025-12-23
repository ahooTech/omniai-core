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

# Paths that do NOT require authentication or tenant context
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
        # Skip tenant/auth checks for public paths
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # Extract JWT token from Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": {"code": "MISSING_AUTH_TOKEN", "message": "Authorization header missing or invalid"}}
            )

        token = auth_header[7:]  # Remove "Bearer "

        try:
            # Decode and validate JWT
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            email = payload.get("sub")
            tenant_id = payload.get("tenant")

            if not email or not tenant_id:
                raise JWTError("Missing required claims")

            # ✅ TRUSTED: tenant_id comes from signed JWT, not client header
            request.state.tenant_id = tenant_id
            request.state.user_email = email

        except JWTError:
            return JSONResponse(
                status_code=401,
                content={"error": {"code": "INVALID_TOKEN", "message": "Invalid or expired token"}}
            )

        response = await call_next(request)
        return response