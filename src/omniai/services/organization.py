
# src/omniai/services/organization.py

"""
Organization service layer.
Used by:
- Auth (user signup)
- Org management (manual creation, invites, deletion)
"""

import re
import unicodedata
from typing import Optional
from sqlalchemy import insert, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from omniai.core.logging import logger
from omniai.models.organization import Organization
from omniai.models.user import User, user_organization


def slugify(value: str, max_length: int = 50) -> str:
    """Convert 'My Org!' → 'my-org' (safe for URLs)"""
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    slug = re.sub(r'[-\s]+', '-', value).strip('-_')
    return slug[:max_length]


async def create_organization_for_user(
    db: AsyncSession,
    user_id: str,
    name: str,
    set_as_default: bool = False
) -> Organization:
    """
    Creates an organization and links user as owner.
    Used during signup (set_as_default=True) and manual creation (False).
    """
    logger.debug("create_organization_for_user_start", name=name, user_id=user_id)

    # Generate unique slug
    base_slug = slugify(name)
    slug = base_slug
    counter = 1
    while True:
        result = await db.execute(select(Organization).where(Organization.slug == slug))
        if not result.scalars().first():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1
        if counter > 100:
            logger.error("slug_generation_failed", name=name, base_slug=base_slug)
            raise ValueError("Could not generate unique slug")

    # Create org
    org = Organization(name=name, slug=slug)
    db.add(org)
    await db.flush()
    logger.debug("org_created", org_id=org.id, slug=slug)

    # Link user as owner
    await db.execute(
        insert(user_organization).values(
            user_id=user_id,
            organization_id=org.id,
            role="owner",
            is_default=set_as_default
        )
    )
    logger.info("user_linked_to_org", user_id=user_id, org_id=org.id, is_default=set_as_default)
    return org


# --- NEW: Delete Organization Function ---
async def delete_organization(db: AsyncSession, org_id: str, user_id: str) -> None:
    """
    Deletes an organization if:
    - User is the owner
    - It's not a personal organization (slug starts with 'personal-')
    Raises:
        HTTPException(404): If org not found or user not owner
        HTTPException(403): If trying to delete personal org
    """
    # 1. Verify ownership and existence in one query
    result = await db.execute(
        select(Organization)
        .join(user_organization, Organization.id == user_organization.c.organization_id)
        .where(
            Organization.id == org_id,
            user_organization.c.user_id == user_id,
            user_organization.c.role == "owner"
        )
    )
    org = result.scalar_one_or_none()
    
    if not org:
        logger.warning("delete_org_not_found_or_not_owner", org_id=org_id, user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found or you are not the owner"
        )

    # 2. Block deletion of personal orgs
    if org.slug.startswith("personal-"):
        logger.warning("delete_org_blocked_personal", org_id=org_id, slug=org.slug)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete personal organization"
        )

    # 3. Delete the organization (relies on DB FK cascade to clean up memberships)
    await db.execute(delete(Organization).where(Organization.id == org_id))
    await db.commit()
    logger.info("org_deleted", org_id=org_id, user_id=user_id)



# --- NEW: Remove Member Function ---
async def remove_member(
    db: AsyncSession,
    org_id: str,
    current_user_id: str,
    target_user_id: str
) -> None:
    """
    Owner removes a member from the organization.
    - Cannot remove self
    - Cannot remove another owner
    - Cannot remove from personal org
    """
    logger.debug("remove_member_start", org_id=org_id, current_user_id=current_user_id, target_user_id=target_user_id)

    # 1. Verify current user is owner of org
    if not await is_org_owner(db, current_user_id, org_id):
        logger.warning("remove_member_forbidden_not_owner", org_id=org_id, user_id=current_user_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can remove members"
        )

    # 2. Prevent removing self
    if current_user_id == target_user_id:
        logger.warning("remove_member_forbidden_self", user_id=current_user_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself"
        )

    # 3. Get target user's role
    target_role = await get_user_org_role(db, target_user_id, org_id)
    if target_role is None:
        logger.warning("remove_member_target_not_in_org", org_id=org_id, target_user_id=target_user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this organization"
        )

    # 4. Prevent removing other owners
    if target_role == "owner":
        logger.warning("remove_member_forbidden_owner", org_id=org_id, target_user_id=target_user_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove organization owner"
        )

    # 5. Block removal from personal orgs
    org_result = await db.execute(select(Organization.slug).where(Organization.id == org_id))
    org_slug = org_result.scalar_one_or_none()
    if org_slug and org_slug.startswith("personal-"):
        logger.warning("remove_member_forbidden_personal_org", org_id=org_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify personal organization"
        )

    # 6. Remove membership
    await db.execute(
        delete(user_organization)
        .where(
            user_organization.c.organization_id == org_id,
            user_organization.c.user_id == target_user_id
        )
    )
    await db.commit()
    logger.info("member_removed", org_id=org_id, removed_user_id=target_user_id, removed_by=current_user_id)


# --- NEW: Leave Organization Function ---
async def leave_organization(
    db: AsyncSession,
    org_id: str,
    user_id: str
) -> None:
    """
    User leaves an organization.
    - Cannot leave personal org
    - Cannot leave if last owner
    """
    logger.debug("leave_organization_start", org_id=org_id, user_id=user_id)

    # 1. Verify user is member of org
    current_role = await get_user_org_role(db, user_id, org_id)
    if current_role is None:
        logger.warning("leave_org_not_member", org_id=org_id, user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not a member of this organization"
        )

    # 2. Block leaving personal org
    org_result = await db.execute(select(Organization.slug).where(Organization.id == org_id))
    org_slug = org_result.scalar_one_or_none()
    if org_slug and org_slug.startswith("personal-"):
        logger.warning("leave_org_forbidden_personal", org_id=org_id, user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot leave personal organization"
        )

    # 3. If user is owner, ensure at least one other owner exists
    if current_role == "owner":
        # Count other owners
        result = await db.execute(
            select(user_organization.c.user_id)
            .where(
                user_organization.c.organization_id == org_id,
                user_organization.c.role == "owner",
                user_organization.c.user_id != user_id
            )
        )
        other_owners = result.scalars().all()
        if not other_owners:
            logger.warning("leave_org_last_owner", org_id=org_id, user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot leave: you are the last owner of this organization"
            )

    # 4. Remove membership
    await db.execute(
        delete(user_organization)
        .where(
            user_organization.c.organization_id == org_id,
            user_organization.c.user_id == user_id
        )
    )
    await db.commit()
    logger.info("user_left_org", org_id=org_id, user_id=user_id)




# --- Existing role functions (keep these) ---
async def get_user_org_role(db: AsyncSession, user_id: str, org_id: str) -> Optional[str]:
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