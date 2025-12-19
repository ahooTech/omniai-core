from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from omniai.db.session import get_db
from omniai.models.organization import Organization

class TenantValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Extract tenant ID (guard clause 1)
        tenant_id = request.headers.get("x-tenant-id")
        if not tenant_id:
            return JSONResponse(
                status_code=400,
                content={"error": {"code": "MISSING_TENANT_ID", "message": "X-Tenant-ID header is required"}}
            )

        # 2. Validate format (guard clause 2)
        if not self._is_valid_tenant_id(tenant_id):
            return JSONResponse(
                status_code=400,
                content={"error": {"code": "INVALID_TENANT_ID", "message": "Tenant ID must be a non-empty string"}}
            )

        # 3. Fetch tenant from DB
        db = next(get_db())  # simple sync for Phase 1; later async
        tenant = db.query(Organization).filter(Organization.id == tenant_id).first()

        # 4. Ensure tenant exists (guard clause 3)
        if not tenant:
            return JSONResponse(
                status_code=404,
                content={"error": {"code": "TENANT_NOT_FOUND", "message": "No organization found with this ID"}}
            )

        # 5. Attach to request and proceed
        request.state.tenant = tenant
        response = await call_next(request)
        return response

    def _is_valid_tenant_id(self, tid: str) -> bool:
        return isinstance(tid, str) and tid.strip() != ""