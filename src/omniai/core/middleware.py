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

# Listen for ID's e.t.c
from fastapi import Request
# Identify ID's e.t.c
from starlette.middleware.base import BaseHTTPMiddleware
# Respond to user's message
from starlette.responses import JSONResponse

class TenantValidationMiddleware(BaseHTTPMiddleware):
    # Define paths that don't need tenant validation
    EXCLUDED_PATHS = {"/v1/health", "/metrics", "/ready"}

    async def dispatch(self, request: Request, call_next):

         # Skip tenant check for operational endpoints.
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)
        
        # Get raw header value — headers.get() returns None if absent
        tenant_id = request.headers.get("x-tenant-id")

        # 1. MISSING: header not present at all
        if tenant_id is None:
            return JSONResponse(
                status_code=400,
                content={"error": {"code": "MISSING_TENANT_ID", "message": "X-Tenant-ID header is required"}}
            )

        # 2. INVALID: header present but empty or not a valid string
        if not isinstance(tenant_id, str) or tenant_id.strip() == "":
            return JSONResponse(
                status_code=400,
                content={"error": {"code": "INVALID_TENANT_ID", "message": "Tenant ID must be a non-empty string"}}
            )

        # 3. VALID: proceed (later we'll validate existence in DB)
        request.state.tenant_id = tenant_id  # store ID for now; full object later "request.state is  aprivate notepad to remember the ID that made the request as we proceed down the system."
        response = await call_next(request) # takes message to the appropriate handler then returns message to response
        return response
# Fetch tenant ID from database and ensure tenant exists in database