# src/omniai/services/organization.py

""" You’ll use this in:

    Delete org endpoint
    Org settings
    Invite management
    Add logging here later
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from omniai.models.user import user_organization


async def get_user_org_role(db: AsyncSession, user_id: str, org_id: str) -> str | None:
    result = await db.execute(
        select(user_organization.c.role)
        .where(user_organization.c.user_id == user_id)
        .where(user_organization.c.organization_id == org_id)
    )
    row = result.fetchone()
    return row[0] if row else None

async def is_org_owner(db: AsyncSession, user_id: str, org_id: str) -> bool:
    role = await get_user_org_role(db, user_id, org_id)
    return role == "owner"
