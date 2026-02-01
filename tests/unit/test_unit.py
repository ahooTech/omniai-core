import uuid
import pytest
from typing import AsyncGenerator


from sqlalchemy.ext.asyncio import AsyncSession
from omniai.models.user import User, user_organization
from omniai.models.organization import Organization
from omniai.services.auth import get_password_hash

from omniai.services.invite import create_invite, accept_invite
from omniai.api.v1.schemas import InviteCreate
from sqlalchemy import select
from fastapi import HTTPException

from omniai.services.organization import  delete_organization, leave_organization, remove_member


############################################################################################ for unit tests to have a different dp session

# --- IN-MEMORY TEST DB SETUP (self-contained) ---
import asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

# Create in-memory SQLite engine (shared across tests in this file)
_test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
    future=True,
    poolclass=StaticPool,  # Required for in-memory SQLite sharing
)

_TestSessionLocal = async_sessionmaker(
    bind=_test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def _init_test_db():
    from omniai.models.base import Base  # ← Single shared Base
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(scope="session", autouse=True)
def initialize_test_db():
    """Initialize the in-memory test DB once before any test runs."""
    asyncio.run(_init_test_db())

# --- END TEST DB SETUP ---

#############################################################################################################


# tests/unit/test_session.py
@pytest.mark.asyncio
async def test_get_db_yields_session():
    from omniai.db.session import get_db
    """get_db should yield an async session that auto-closes."""
    async for session in get_db():
        assert session is not None
        assert session.is_active  # Session should be active during yield

    # After the async for loop, session should be closed
    # You can't check this directly, but you can verify no exceptions
    # (which implies proper cleanup)


############################################################### testing services/auth.py Testing functions in Isolation

@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Provides a fresh DB session for each test (with rollback)."""
    async with _TestSessionLocal() as session:
        yield session
        await session.rollback()  # Clean up after each test



# Unit test for authenticate_user
@pytest.mark.asyncio
async def test_authenticate_user_success(db):
    from omniai.services.auth import authenticate_user, create_user_with_org
    
    # Create a test user
    email = "auth_test_success@test.com"
    password = "SecurePass123!"
    await create_user_with_org(db, email, password)
    
    # Authenticate
    user = await authenticate_user(db, email, password)
    assert user is not None
    assert user.email == email


@pytest.mark.asyncio
async def test_authenticate_user_invalid_password(db):
    from omniai.services.auth import authenticate_user, create_user_with_org
    
    email = "auth_test_invalid@test.com"
    password = "SecurePass123!"
    await create_user_with_org(db, email, password)
    
    # Wrong password
    user = await authenticate_user(db, email, "WrongPassword123!")
    assert user is None


@pytest.mark.asyncio
async def test_authenticate_user_nonexistent_email(db):
    from omniai.services.auth import authenticate_user
    
    user = await authenticate_user(db, "nonexistent@test.com", "any_password")
    assert user is None


@pytest.mark.asyncio
async def test_create_user_with_org_creates_personal_org(db):
    from omniai.services.auth import create_user_with_org
    from omniai.models.user import User
    from omniai.models.organization import Organization
    from sqlalchemy import select

    email = "unit_test_create@test.com"
    password = "TestPass123!"
    
    user = await create_user_with_org(db, email, password)
    
    # Verify user
    assert user.email == email
    assert user.hashed_password is not None
    
    # Verify org was created
    result = await db.execute(select(Organization).where(Organization.name.like(f"Personal – {email}%")))
    org = result.scalar_one_or_none()
    assert org is not None
    assert org.slug.startswith("personal")
    
    # Verify membership
    from omniai.models.user import user_organization
    result = await db.execute(
        select(user_organization)
        .where(user_organization.c.user_id == user.id)
        .where(user_organization.c.organization_id == org.id)
    )
    membership = result.fetchone()
    assert membership is not None
    assert membership.is_default is True
    assert membership.role == "owner"


# Make slug to always exist in db so that we loop 100+ times to trigger error "Could not generate a unique slug for Personal org""

@pytest.mark.asyncio
async def test_create_user_with_org_fails_after_100_slug_attempts(db):
    from omniai.services.auth import create_user_with_org
    from omniai.models.organization import Organization

    # Create 100 orgs with slug "personal-test-collision"
    base_name = "Personal – test-collision@test.com"
    for i in range(100):
        if i == 0:
            slug = "personal-test-collisiontestcom"
        else:
            slug = f"personal-test-collisiontestcom-{i}"
        org = Organization(name=f"{base_name} {i}", slug=slug)
        db.add(org)
    await db.commit()

    email = "test-collision@test.com"
    password = "TestPass123!"

    with pytest.raises(ValueError, match="Could not generate unique slug"):
        await create_user_with_org(db, email, password)



###############################################################
# Unit tests for services/organization.py
###############################################################

@pytest.mark.asyncio
async def test_get_user_org_role_returns_role(db):
    from omniai.services.organization import get_user_org_role
    from omniai.models.user import User, user_organization
    from omniai.models.organization import Organization

    # Create user and org
    user = User(email="org_test@test.com", hashed_password="x")
    org = Organization(name="Test Org", slug="test-org")
    
    db.add(user)
    db.add(org)
    await db.flush()

    # Link with role "member"
    await db.execute(
        user_organization.insert().values(
            user_id=user.id,
            organization_id=org.id,
            role="member"
        )
    )
    await db.commit()

    # Test
    role = await get_user_org_role(db, str(user.id), str(org.id))
    assert role == "member"


@pytest.mark.asyncio
async def test_get_user_org_role_returns_none_if_no_membership(db):
    from omniai.services.organization import get_user_org_role
    from omniai.models.user import User
    from omniai.models.organization import Organization

    user = User(email="no_member@test.com", hashed_password="x")
    org = Organization(name="Lonely Org", slug="lonely")

    db.add(user)
    db.add(org)
    await db.flush()
    
    await db.commit()

    role = await get_user_org_role(db, str(user.id), str(org.id))
    assert role is None


@pytest.mark.asyncio
async def test_is_org_owner_returns_true_if_owner(db):
    from omniai.services.organization import is_org_owner
    from omniai.models.user import User, user_organization
    from omniai.models.organization import Organization

    user = User(email="owner@test.com", hashed_password="x")
    org = Organization(name="My Org", slug="my-org")

    db.add(user)
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=user.id,
            organization_id=org.id,
            role="owner"
        )
    )
    await db.commit()

    assert await is_org_owner(db, str(user.id), str(org.id)) is True


@pytest.mark.asyncio
async def test_is_org_owner_returns_false_if_not_owner(db):
    from omniai.services.organization import is_org_owner
    from omniai.models.user import User, user_organization
    from omniai.models.organization import Organization

    user = User(email="not_owner@test.com", hashed_password="x")
    org = Organization(name="Not Mine", slug="not-mine")

    db.add(user)
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=user.id,
            organization_id=org.id,
            role="member"  # ← not owner
        )
    )
    await db.commit()

    assert await is_org_owner(db, str(user.id), str(org.id)) is False

############################################### New

@pytest.mark.asyncio
async def test_remove_member_forbidden_not_owner(db):
    # Setup: owner + org
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    owner = User(email=owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner)
    await db.flush()

    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )
    await db.commit()

    # Non-owner tries to remove a member
    non_owner_email = f"nonowner_{uuid.uuid4().hex}@test.com"
    non_owner = User(email=non_owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(non_owner)
    await db.flush()

    with pytest.raises(HTTPException) as exc:
        await remove_member(db, org.id, non_owner.id, owner.id)
    
    assert exc.value.status_code == 403
    assert "Only owners can remove members" in exc.value.detail


@pytest.mark.asyncio
async def test_remove_member_forbidden_self(db):
    # Setup: owner + org
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    owner = User(email=owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner)
    await db.flush()

    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )
    await db.commit()

    # Owner tries to remove themselves
    with pytest.raises(HTTPException) as exc:
        await remove_member(db, org.id, owner.id, owner.id)
    
    assert exc.value.status_code == 400
    assert "Cannot remove yourself" in exc.value.detail


@pytest.mark.asyncio
async def test_leave_organization_forbidden_personal(db):
    # Setup: user + personal org
    user_email = f"user_{uuid.uuid4().hex}@test.com"
    user = User(email=user_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(user)
    await db.flush()

    # Personal org (slug starts with "personal-")
    personal_slug = f"personal-{uuid.uuid4().hex}"
    org = Organization(name="Personal", slug=personal_slug)
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=user.id,
            organization_id=org.id,
            role="owner",
            is_default=True
        )
    )
    await db.commit()

    # User tries to leave personal org
    with pytest.raises(HTTPException) as exc:
        await leave_organization(db, org.id, user.id)
    
    assert exc.value.status_code == 403
    assert "Cannot leave personal organization" in exc.value.detail


@pytest.mark.asyncio
async def test_leave_organization_last_owner(db):
    # Setup: single owner + org
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    owner = User(email=owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner)
    await db.flush()

    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )
    await db.commit()

    # Owner tries to leave — should fail (last owner)
    with pytest.raises(HTTPException) as exc:
        await leave_organization(db, org.id, owner.id)
    
    assert exc.value.status_code == 400
    assert "you are the last owner" in exc.value.detail.lower()


##


@pytest.mark.asyncio
async def test_remove_member_target_not_in_org(db):
    # Setup: owner + org
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    owner = User(email=owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner)
    await db.flush()

    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )
    await db.commit()

    # Try to remove a user who is NOT in the org
    fake_user_id = "usr_1234567890abcdef1234567890abcdef"
    with pytest.raises(HTTPException) as exc:
        await remove_member(db, org.id, owner.id, fake_user_id)
    
    assert exc.value.status_code == 404
    assert "User is not a member of this organization" in exc.value.detail


@pytest.mark.asyncio
async def test_remove_member_forbidden_owner(db):
    # Setup: two owners in one org
    owner1_email = f"owner1_{uuid.uuid4().hex}@test.com"
    owner1 = User(email=owner1_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner1)
    await db.flush()

    owner2_email = f"owner2_{uuid.uuid4().hex}@test.com"
    owner2 = User(email=owner2_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner2)
    await db.flush()

    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    # Link both as owners
    await db.execute(
        user_organization.insert().values(
            user_id=owner1.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )
    await db.execute(
        user_organization.insert().values(
            user_id=owner2.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )
    await db.commit()

    # owner1 tries to remove owner2 → should fail
    with pytest.raises(HTTPException) as exc:
        await remove_member(db, org.id, owner1.id, owner2.id)
    
    assert exc.value.status_code == 400
    assert "Cannot remove organization owner" in exc.value.detail


@pytest.mark.asyncio
async def test_leave_organization_not_member(db):
    # Setup: user + org (user is NOT a member)
    user_email = f"user_{uuid.uuid4().hex}@test.com"
    user = User(email=user_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(user)
    await db.flush()

    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    # User is NOT linked to org
    await db.commit()

    # User tries to leave → should fail
    with pytest.raises(HTTPException) as exc:
        await leave_organization(db, org.id, user.id)
    
    assert exc.value.status_code == 404
    assert "You are not a member of this organization" in exc.value.detail


@pytest.mark.asyncio
async def test_leave_organization_success_with_other_owner(db):
    # Setup: 2 owners in one org
    owner1_email = f"owner1_{uuid.uuid4().hex}@test.com"
    owner1 = User(email=owner1_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner1)
    await db.flush()

    owner2_email = f"owner2_{uuid.uuid4().hex}@test.com"
    owner2 = User(email=owner2_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner2)
    await db.flush()

    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    # Link both as owners
    await db.execute(
        user_organization.insert().values(
            user_id=owner1.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )
    await db.execute(
        user_organization.insert().values(
            user_id=owner2.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )
    await db.commit()

    # Owner1 leaves → should succeed (Owner2 remains)
    await leave_organization(db, org.id, owner1.id)

    # Verify Owner1 is gone, Owner2 remains
    result = await db.execute(
        select(user_organization.c.user_id, user_organization.c.role)
        .where(user_organization.c.organization_id == org.id)
    )
    memberships = result.fetchall()
    user_ids = [m[0] for m in memberships]
    roles = [m[1] for m in memberships]

    assert owner1.id not in user_ids
    assert owner2.id in user_ids
    assert "owner" in roles
    
####

@pytest.mark.asyncio
async def test_delete_organization_not_owner(db):
    owner = User(
        email=f"user_{uuid.uuid4().hex}@test.com",
        hashed_password="x"
    )
    db.add(owner)
    await db.flush()

    # IMPORTANT: unique slug to avoid collisions
    org = Organization(
        name="Test Org",
        slug=f"test-org-{uuid.uuid4().hex}"
    )
    db.add(org)
    await db.flush()
    await db.commit()

    # User is NOT linked as owner → should be treated as not found
    with pytest.raises(HTTPException) as exc:
        await delete_organization(db, org.id, owner.id)

    assert exc.value.status_code == 404
    assert "not found or you are not the owner" in exc.value.detail.lower()



@pytest.mark.asyncio
async def test_delete_organization_personal_forbidden(db):
    owner = User(email=f"user_{uuid.uuid4().hex}@test.com", hashed_password="x")
    db.add(owner)
    await db.flush()

    org = Organization(name="Personal", slug=f"personal-{uuid.uuid4().hex}")
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=True
        )
    )
    await db.commit()

    with pytest.raises(HTTPException) as exc:
        await delete_organization(db, org.id, owner.id)

    assert exc.value.status_code == 403



@pytest.mark.asyncio
async def test_delete_organization_success(db):
    owner = User(email=f"user_{uuid.uuid4().hex}@test.com", hashed_password="x")
    db.add(owner)
    await db.flush()

    org = Organization(name="Test Org", slug=f"test-{uuid.uuid4().hex}")
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )
    await db.commit()

    await delete_organization(db, org.id, owner.id)

    result = await db.execute(
        select(Organization).where(Organization.id == org.id)
    )
    assert result.scalar_one_or_none() is None




@pytest.mark.asyncio
async def test_remove_member_forbidden_personal_org(db):
    owner = User(email=f"owner_{uuid.uuid4().hex}@test.com", hashed_password="x")
    member = User(email=f"member_{uuid.uuid4().hex}@test.com", hashed_password="x")
    db.add_all([owner, member])
    await db.flush()

    org = Organization(name="Personal", slug=f"personal-{uuid.uuid4().hex}")
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=True
        )
    )
    await db.execute(
        user_organization.insert().values(
            user_id=member.id,
            organization_id=org.id,
            role="member",
            is_default=False
        )
    )
    await db.commit()

    with pytest.raises(HTTPException) as exc:
        await remove_member(db, org.id, owner.id, member.id)

    assert exc.value.status_code == 403
    assert "personal organization" in exc.value.detail.lower()



@pytest.mark.asyncio
async def test_remove_member_success(db):
    # Create owner
    owner = User(
        email=f"owner_{uuid.uuid4().hex}@test.com",
        hashed_password="x"
    )
    db.add(owner)
    await db.flush()

    # Create member
    member = User(
        email=f"member_{uuid.uuid4().hex}@test.com",
        hashed_password="x"
    )
    db.add(member)
    await db.flush()

    # Create org (NOT personal)
    org = Organization(
        name="Test Org",
        slug=f"test-org-{uuid.uuid4().hex}"
    )
    db.add(org)
    await db.flush()

    # Link owner
    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )

    # Link member
    await db.execute(
        user_organization.insert().values(
            user_id=member.id,
            organization_id=org.id,
            role="member",
            is_default=False
        )
    )
    await db.commit()

    # Act: owner removes member
    await remove_member(db, org.id, owner.id, member.id)

    # Assert: member is gone
    result = await db.execute(
        select(user_organization.c.user_id)
        .where(user_organization.c.organization_id == org.id)
    )
    remaining_user_ids = [row[0] for row in result.fetchall()]

    assert member.id not in remaining_user_ids
    assert owner.id in remaining_user_ids


###############################################################
# Unit tests for src/omniai/services/invite.py
###############################################################

@pytest.mark.asyncio
async def test_create_invite_success(db):
    # Create owner (no commit)
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    hashed_pw = get_password_hash("SecurePass123!")
    owner = User(email=owner_email, hashed_password=hashed_pw)
    db.add(owner)
    await db.flush()

    # Create org with UNIQUE slug
    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    # Link owner to org
    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )

    # Create invite
    invitee_email = f"invitee_{uuid.uuid4().hex}@test.com"
    invite_data = InviteCreate(email=invitee_email)
    invite = await create_invite(db, org.id, owner.id, invite_data)

    assert invite.email == invitee_email
    assert invite.organization_id == org.id
    assert invite.invited_by_id == owner.id
    assert len(invite.token) > 20


@pytest.mark.asyncio
async def test_create_invite_forbidden_not_owner(db):
    # Owner
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    owner = User(email=owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner)
    await db.flush()

    # Non-owner
    non_owner_email = f"nonowner_{uuid.uuid4().hex}@test.com"
    non_owner = User(email=non_owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(non_owner)
    await db.flush()

    # Org owned by owner (UNIQUE slug)
    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )

    # Non-owner tries to invite → should fail
    invite_data = InviteCreate(email="newuser@example.com")
    with pytest.raises(HTTPException) as exc:
        await create_invite(db, org.id, non_owner.id, invite_data)
    
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_accept_invite_success(db):
    # Owner
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    owner = User(email=owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner)
    await db.flush()

    # Org (UNIQUE slug)
    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )

    # Member
    member_email = f"member_{uuid.uuid4().hex}@test.com"
    member = User(email=member_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(member)
    await db.flush()

    # Create invite
    invite_data = InviteCreate(email=member_email)
    invite = await create_invite(db, org.id, owner.id, invite_data)

    # Accept invite
    await accept_invite(db, invite.token, member.id)

    # Verify membership
    result = await db.execute(
        select(user_organization.c.role)
        .where(
            user_organization.c.user_id == member.id,
            user_organization.c.organization_id == org.id
        )
    )
    role = result.scalar_one_or_none()
    assert role == "member"


@pytest.mark.asyncio
async def test_accept_invite_invalid_token(db):

    with pytest.raises(HTTPException) as exc:
        await accept_invite(db, "invalid-token", "usr_123")
    
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_create_invite_user_already_member(db):

    # Create owner + org
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    owner = User(email=owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner)
    await db.flush()

    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )

    # Try to invite the *same* user again
    invite_data = InviteCreate(email=owner_email)
    with pytest.raises(HTTPException) as exc:
        await create_invite(db, org.id, owner.id, invite_data)
    
    assert exc.value.status_code == 400
    assert "already a member" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_accept_invite_email_mismatch(db):

    # Owner + org
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    owner = User(email=owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner)
    await db.flush()

    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )

    # Create invite for *another* email
    invitee_email = "invitee@test.com"
    invite_data = InviteCreate(email=invitee_email)
    invite = await create_invite(db, org.id, owner.id, invite_data)

    # Now try to accept with a *different* user (email mismatch)
    member_email = "mismatch@test.com"
    member = User(email=member_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(member)
    await db.flush()

    with pytest.raises(HTTPException) as exc:
        await accept_invite(db, invite.token, member.id)
    
    assert exc.value.status_code == 400
    assert "does not match your account" in exc.value.detail


@pytest.mark.asyncio
async def test_accept_invite_user_not_found(db):

    # Create owner manually (no personal org)
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    owner = User(email=owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner)
    await db.flush()

    # Create org manually
    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    # Link owner to org
    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )

    # Create invite
    invitee_email = f"invitee_{uuid.uuid4().hex}@test.com"
    invite_data = InviteCreate(email=invitee_email)
    invite = await create_invite(db, org.id, owner.id, invite_data)

    # Try to accept with a *non-existent* user ID
    non_existent_user_id = "usr_1234567890abcdef1234567890abcdef"
    with pytest.raises(HTTPException) as exc:
        await accept_invite(db, invite.token, non_existent_user_id)
    
    assert exc.value.status_code == 404
    assert "User not found" in exc.value.detail

####################################New