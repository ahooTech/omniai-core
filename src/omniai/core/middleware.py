
# OMNIAI Core Middleware Layer
from typing import Awaitable, Callable

from fastapi import Request
from jwt import PyJWTError
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from structlog.contextvars import bind_contextvars

from omniai.core.jwt import decode_token
from omniai.core.logging import logger
from omniai.db.session import AsyncSessionLocal
from omniai.models.organization import Organization
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
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # === STEP 1: Authenticate user via JWT ===
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warn("auth_missing", url=str(request.url))
            return JSONResponse(
                status_code=401,
                content={"error": {"code": "MISSING_AUTH_TOKEN", "message": "Authorization header missing"}}
            )

        token = auth_header[7:]
        try:
            payload = decode_token(token)
            user_id = payload["sub"]
        except PyJWTError as e:
            logger.warn("auth_invalid_token", url=str(request.url), error=str(e))
            return JSONResponse(
                status_code=401,
                content={"error": {"code": "INVALID_TOKEN", "message": "Invalid or expired token"}}
            )

        # === STEP 2–3: Handle tenant resolution + validation in ONE DB session ===
        tenant_id = request.headers.get("x-tenant-id")
        used_default = False

        async with AsyncSessionLocal() as db:
            # --- Resolve tenant_id if missing ---
            if not tenant_id:
                logger.info("tenant_missing_fallback_to_default", user_id=user_id)
                result = await db.execute(
                    select(user_organization.c.organization_id)
                    .where(
                        user_organization.c.user_id == user_id,
                        user_organization.c.is_default
                    )
                )
                default_org = result.scalar_one_or_none()
                if not default_org:
                    logger.warn("user_no_default_org", user_id=user_id)
                    return JSONResponse(
                        status_code=403,
                        content={"error": {"code": "NO_DEFAULT_ORG", "message": "User has no default organization."}}
                    )
                tenant_id = default_org
                used_default = True
            else:
                # --- Validate org exists ---
                org_exists = await db.execute(
                    select(Organization.id).where(Organization.id == tenant_id)
                )
                if org_exists.scalar_one_or_none() is None:
                    logger.warn("tenant_not_found", tenant_id=tenant_id, user_id=user_id)
                    return JSONResponse(
                        status_code=404,
                        content={"error": {"code": "ORG_NOT_FOUND", "message": "Organization not found"}}
                    )

            # --- Validate user is a member of the resolved tenant_id ---
            membership = await db.execute(
                select(user_organization.c.organization_id)
                .where(
                    user_organization.c.user_id == user_id,
                    user_organization.c.organization_id == tenant_id
                )
            )
            if membership.scalar_one_or_none() is None:
                logger.warn("access_denied_not_org_member", user_id=user_id, tenant_id=tenant_id)
                return JSONResponse(
                    status_code=403,
                    content={"error": {"code": "NOT_ORG_MEMBER", "message": "Not a member of the specified organization"}}
                )

        # === STEP 4: Bind to logs and request state ===
        bind_contextvars(user_id=user_id, tenant_id=tenant_id)
        request.state.user_id = user_id
        request.state.tenant_id = tenant_id

        logger.info(
            "auth_and_tenant_success",
            user_id=user_id,
            tenant_id=tenant_id,
            used_default=used_default
        )

        return await call_next(request)
