# src/omniai/services/invite.py
"""
Invite service layer.
Used by:
- Organization owners to invite members
- Users to accept invites and join organizations
"""

import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from omniai.api.v1.schemas import InviteCreate  # ✅ Matches your schema location
from omniai.core.logging import logger          # ✅ Your structured logger
from omniai.models.invite import Invite
from omniai.models.organization import Organization
from omniai.models.user import User, user_organization


async def create_invite(
    db: AsyncSession,
    org_id: str,
    inviter_id: str,
    invite_data: InviteCreate
) -> Invite:
    """
    Creates an invite for a user to join an organization.
    Only org owners can send invites.
    """
    logger.debug("create_invite_start", org_id=org_id, inviter_id=inviter_id, email=invite_data.email)

    # 1. Verify inviter is owner of org
    result = await db.execute(
        select(Organization)
        .join(user_organization, Organization.id == user_organization.c.organization_id)
        .where(
            Organization.id == org_id,
            user_organization.c.user_id == inviter_id,
            user_organization.c.role == "owner"
        )
    )
    org = result.scalar_one_or_none()
    if not org:
        logger.warning("create_invite_forbidden", org_id=org_id, user_id=inviter_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can send invites"
        )

    # 2. Check if user already in org
    user_result = await db.execute(select(User.id).where(User.email == invite_data.email))
    invited_user_id = user_result.scalar_one_or_none()
    
    if invited_user_id:
        membership_result = await db.execute(
            select(user_organization.c.user_id)
            .where(
                user_organization.c.organization_id == org_id,
                user_organization.c.user_id == invited_user_id
            )
        )
        if membership_result.scalar_one_or_none():
            logger.warning("create_invite_user_already_member", org_id=org_id, email=invite_data.email)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this organization"
            )

    # 3. Generate token
    token = secrets.token_urlsafe(32)

    # 4. Create invite
    invite = Invite(
        token=token,
        email=invite_data.email,
        organization_id=org_id,
        invited_by_id=inviter_id
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    
    logger.info("invite_created", invite_id=invite.id, org_id=org_id, email=invite_data.email)
    return invite


async def accept_invite(db: AsyncSession, token: str, user_id: str) -> None:
    """
    Accepts an invite and adds the user to the organization as a member.
    """
    logger.debug("accept_invite_start", token=token, user_id=user_id)

    # 1. Find active, unexpired invite
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Invite)
        .where(
            Invite.token == token,
            Invite.is_active,
            Invite.expires_at > now,
            Invite.accepted_at.is_(None)
        )
    )

    invite = result.scalar_one_or_none()
    if not invite:
        logger.warning("accept_invite_invalid", token=token)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invite"
        )

    # 2. Get user email
    user_result = await db.execute(select(User.email).where(User.id == user_id))
    user_email = user_result.scalar_one_or_none()
    if not user_email:
        logger.error("accept_invite_user_not_found", user_id=user_id)
        raise HTTPException(status_code=404, detail="User not found")

    # 3. Verify email matches
    if user_email != invite.email:
        logger.warning("accept_invite_email_mismatch", invite_email=invite.email, user_email=user_email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite email does not match your account"
        )

    # 4. Add to org as member
    await db.execute(
        user_organization.insert().values(
            user_id=user_id,
            organization_id=invite.organization_id,
            role="member",
            is_default=False
        )
    )

    # 5. Mark invite as accepted
    await db.execute(
        update(Invite)
        .where(Invite.id == invite.id)
        .values(accepted_at=now, is_active=False)
    )
    await db.commit()
    
    logger.info("invite_accepted", invite_id=invite.id, user_id=user_id, org_id=invite.organization_id)