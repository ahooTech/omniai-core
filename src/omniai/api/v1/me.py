# src/omniai/api/v1/me.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from omniai.db.session import get_db
from omniai.models.user import User
from omniai.api.v1.schemas import UserMe

router = APIRouter()

@router.get("/me", response_model=UserMe)
async def read_users_me(
    request: Request,  # ← Get the enriched request
    db: AsyncSession = Depends(get_db)
):
    tenant_id = getattr(request.state, "tenant_id", None)
    user_email = getattr(request.state, "user_email", None)

    if not tenant_id or not user_email:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Fetch user — but now we TRUST tenant_id from middleware
    result = await db.execute(select(User).where(User.email == user_email))
    user = result.scalar_one_or_none()

    if not user or user.organization_id != tenant_id:
        # This should NEVER happen if middleware is correct — but still safe
        raise HTTPException(status_code=401, detail="User-tenant mismatch")

    return UserMe(
        id=user.id,
        email=user.email,
        organization_id=user.default_organization_id,
        # Later, you can add: orgs: List[OrgSummary]
    )