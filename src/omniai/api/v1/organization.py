
# src/omniai/api/v1/organization.py
from fastapi import APIRouter, Depends, status, Path, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from omniai.models.user import User
from omniai.services.organization import create_organization_for_user, delete_organization
from omniai.api.v1.schemas import OrganizationCreate, OrganizationSummary
from omniai.api.deps import get_current_user
from omniai.db.session import get_db
from typing import List
from omniai.services.organization import remove_member, leave_organization

router = APIRouter()

@router.post("", response_model=OrganizationSummary, status_code=status.HTTP_201_CREATED)
async def create_organization_endpoint(
    org_in: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> OrganizationSummary:
    org = await create_organization_for_user(
        db, 
        user_id=current_user.id, 
        name=org_in.name, 
        set_as_default=False
    )

    await db.commit()
    await db.refresh(org)
    
    return OrganizationSummary(
        id=org.id,
        name=org.name,
        slug=org.slug,
        role="owner",
        is_default=False
    )




# ✅ NEW: Delete Organization Endpoint
@router.delete(
    "/{org_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Organization deleted successfully"},
        403: {"description": "Cannot delete personal organization"},
        404: {"description": "Organization not found or you are not the owner"}
    }
)
async def delete_organization_endpoint(
    org_id: str = Path(..., description="The ID of the organization to delete"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete an organization.
    - Only owners can delete
    - Personal organizations (slug starts with 'personal-') cannot be deleted
    """
    await delete_organization(db=db, org_id=org_id, user_id=current_user.id)
    # Returns 204 No Content automatically


# ADD THIS FUNCTION BELOW YOUR EXISTING ONES
@router.get("", response_model=List[OrganizationSummary])
async def list_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[OrganizationSummary]:
    """
    Get all organizations the current user belongs to.
    """
    from sqlalchemy import select
    from omniai.models.user import user_organization
    from omniai.models.organization import Organization

    # Join to get orgs + membership info
    result = await db.execute(
        select(
            Organization.id,
            Organization.name,
            Organization.slug,
            user_organization.c.role,
            user_organization.c.is_default
        )
        .select_from(Organization)
        .join(user_organization, Organization.id == user_organization.c.organization_id)
        .where(user_organization.c.user_id == current_user.id)
        .order_by(user_organization.c.joined_at.desc())
    )
    
    rows = result.fetchall()
    return [
        OrganizationSummary(
            id=row.id,
            name=row.name,
            slug=row.slug,
            role=row.role,
            is_default=row.is_default
        )
        for row in rows
    ]


# ✅ NEW: Remove Member Endpoint
@router.delete("/{org_id}/members/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member_endpoint(
    org_id: str = Path(..., description="Organization ID"),
    target_user_id: str = Path(..., description="User ID to remove"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Owner removes a member from the organization.
    - Cannot remove self
    - Cannot remove other owners
    - Cannot modify personal org
    """
    await remove_member(db, org_id, current_user.id, target_user_id)


# ✅ NEW: Leave Organization Endpoint
@router.post("/{org_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_organization_endpoint(
    org_id: str = Path(..., description="Organization ID to leave"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Member leaves an organization.
    - Cannot leave personal org
    - Cannot leave if last owner
    """
    await leave_organization(db, org_id, current_user.id)