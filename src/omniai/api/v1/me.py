# src/omniai/api/v1/me.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from omniai.api.v1.schemas import OrganizationSummary, UserMe
from omniai.core.logging import logger
from omniai.db.session import get_db
from omniai.models.organization import Organization
from omniai.models.user import User, user_organization

router = APIRouter()

@router.get("/me", response_model=UserMe)
async def read_users_me(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user_id = getattr(request.state, "user_id", None)
    tenant_id = getattr(request.state, "tenant_id", None)

    if not user_id or not tenant_id:
        logger.warn("me_request_missing_context", url=str(request.url))
        raise HTTPException(status_code=401, detail="Authentication required")

    # 1. Fetch user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        logger.warn("me_request_user_not_found")
        raise HTTPException(status_code=401, detail="User not found")

    # 2. Verify user is member of tenant_id AND get role
    membership_result = await db.execute(
        select(user_organization.c.is_default, user_organization.c.role)
        .where(
            user_organization.c.user_id == user_id,
            user_organization.c.organization_id == tenant_id
        )
    )
    membership = membership_result.fetchone()
    if not membership:
        logger.warn("me_request_not_org_member")
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    role = membership.role

    # 3. Fetch all orgs for user
    orgs_result = await db.execute(
        select(Organization.id, Organization.name, Organization.slug, user_organization.c.role, user_organization.c.is_default)
        .join(user_organization, Organization.id == user_organization.c.organization_id)
        .where(user_organization.c.user_id == user_id)
    )
    orgs = orgs_result.fetchall()
    organizations = [
        OrganizationSummary(
            id=org.id,
            name=org.name,
            slug=org.slug,
            role=org.role,
            is_default=org.is_default
        )
        for org in orgs
    ]

    # ✅ Log successful profile fetch
    logger.info(
        "user_profile_fetched",
        role_in_active_org=role,
        total_organizations=len(organizations)
    )

    return UserMe(
        id=user.id,
        email=user.email,
        active_organization_id=tenant_id,
        role_in_active_org=role,
        organizations=organizations
    )
