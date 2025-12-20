from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class TenantValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
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
        request.state.tenant_id = tenant_id  # store ID for now; full object later
        response = await call_next(request)
        return response
# Fetch tenant ID from database and ensure tenant exists in database