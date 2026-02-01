# src/omniai/api/v1/invites.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from omniai.api.deps import get_current_user
from omniai.db.session import get_db
from omniai.api.v1.schemas import InviteCreate, InviteAccept, InviteResponse
from omniai.services.invite import create_invite, accept_invite
from omniai.models.user import User

router = APIRouter()

"""
@router.post("/organizations/{org_id}/invite", response_model=InviteResponse)
async def send_invite(
    org_id: str,
    invite_data: InviteCreate,  # ✅ FIXED: added ":"
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> InviteResponse:
    #Send an invite to join an organization.
    #Only owners can send invites.
    invite = await create_invite(db, org_id, current_user.id, invite_data)
    return {"invite_id": invite.id, "token": invite.token}
"""

@router.post("/organizations/{org_id}/invite", response_model=InviteResponse)
async def send_invite(
    org_id: str,
    invite_data: InviteCreate,  # ✅ CORRECT: parameter_name: Type
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> InviteResponse:
    """
    Send an invite to join an organization.
    Only owners can send invites.
    """
    invite = await create_invite(db, org_id, current_user.id, invite_data)
    return InviteResponse(invite_id=invite.id, token=invite.token)


@router.post("/invites/accept")
async def accept_invite_endpoint(
    invite_data: InviteAccept,  # ✅ FIXED: added ":"
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    """
    Accept an invite and join the organization as a member.
    """
    await accept_invite(db, invite_data.token, current_user.id)
    return {"message": "Successfully joined organization"}