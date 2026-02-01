# omniai/core/limiter.py
"""
import os
from functools import wraps
from typing import Callable, Any, Coroutine, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

# Global flag Check if rate limiting is disabled
DISABLE_RATE_LIMIT = os.getenv("OMNIAI_DISABLE_RATE_LIMIT", "0").lower() in ("1", "true", "yes")


# Get Redis URL (optional — if not set, falls back to in-memory)
REDIS_URL = os.getenv("REDIS_URL")

# Define _real_limiter as a module-level global — conditionally
_real_limiter: Optional[Limiter] = None

if not DISABLE_RATE_LIMIT:
    # Real limiter (only used if enabled) &&
    # Use Redis if available, otherwise in-memory (not recommended for prod)
    storage_uri = REDIS_URL if REDIS_URL else None
    _real_limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=storage_uri  # ← This enables Redis!
    )

def conditional_limit(limit: str) -> Callable[..., Callable[..., Coroutine[Any, Any, Any]]]:
    #Apply rate limit only if OMNIAI_DISABLE_RATE_LIMIT is not set.
    if DISABLE_RATE_LIMIT or _real_limiter is None:
        def decorator(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Coroutine[Any, Any, Any]]:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    else:
        return _real_limiter.limit(limit)

# Expose limiter instance for app integration
limiter = _real_limiter

"""
"""
# src/omniai/core/limiter.py
import os
from functools import wraps
from typing import Callable, Any, Coroutine, Optional, TypeVar, cast
from slowapi import Limiter
from slowapi.util import get_remote_address
from urllib.parse import urlparse

DISABLE_RATE_LIMIT = os.getenv("OMNIAI_DISABLE_RATE_LIMIT", "0").lower() in ("1", "true", "yes")
REDIS_URL = os.getenv("REDIS_URL")

_real_limiter: Optional[Limiter] = None

if not DISABLE_RATE_LIMIT:
    if REDIS_URL:
        parsed = urlparse(REDIS_URL)
        if parsed.scheme == "rediss":
            # Convert rediss:// → redis://
            storage_uri = f"redis://{parsed.hostname}:{parsed.port or 6379}"
            # Use STRING VALUES that redis-py will parse correctly
            _real_limiter = Limiter(
                key_func=get_remote_address,
                storage_uri=storage_uri,
                storage_options={
                    "ssl": "True",          # ← STRING "True"
                    "ssl_cert_reqs": "none" # ← STRING "none"
                }
            )
        else:
            _real_limiter = Limiter(
                key_func=get_remote_address,
                storage_uri=REDIS_URL
            )
    else:
        _real_limiter = Limiter(key_func=get_remote_address)

# --- Decorator (unchanged) ---
F = TypeVar("F", bound=Callable[..., Coroutine[Any, Any, Any]])

def conditional_limit(limit: str) -> Callable[[F], F]:
    if DISABLE_RATE_LIMIT or _real_limiter is None:
        def decorator(func: F) -> F:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                return await func(*args, **kwargs)
            return cast(F, wrapper)
        return decorator
    else:
        return _real_limiter.limit(limit)

limiter = _real_limiter

"""


"""
import os
from functools import wraps
from typing import Any, Callable, Coroutine, Optional, TypeVar, cast

from slowapi import Limiter
from slowapi.util import get_remote_address

DISABLE_RATE_LIMIT = os.getenv("OMNIAI_DISABLE_RATE_LIMIT", "0").lower() in ("1", "true", "yes")
REDIS_URL = os.getenv("REDIS_URL")

_real_limiter: Optional[Limiter] = None

if not DISABLE_RATE_LIMIT:
    if REDIS_URL:
        # ✅ Use the URL AS-IS — no modification
        _real_limiter = Limiter(
            key_func=get_remote_address,
            storage_uri=REDIS_URL  # ← Just pass it directly
        )
    else:
        _real_limiter = Limiter(key_func=get_remote_address)

F = TypeVar("F", bound=Callable[..., Coroutine[Any, Any, Any]])

def conditional_limit(limit: str) -> Callable[[F], F]:
    if DISABLE_RATE_LIMIT or _real_limiter is None:
        def decorator(func: F) -> F:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                return await func(*args, **kwargs)
            return cast(F, wrapper)
        return decorator
    else:
        return _real_limiter.limit(limit)

limiter = _real_limiter





"""



# Main.py

"""
# 🔒 Security & config audit at startup
logger.info(
    "application_startup_init",
    version="1.0",
    database_engine="postgresql",
    async_driver="asyncpg",
    token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    jwt_algorithm=settings.JWT_ALGORITHM,
    debug_mode=(len(settings.JWT_SECRET_KEY) < 32)
)

if len(settings.JWT_SECRET_KEY) < 32:
    logger.critical(
        "security_risk_weak_jwt_secret",
        message="JWT_SECRET_KEY is less than 32 bytes — rotate immediately!"
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Initialize readiness flag
    app.state.ready = False

    # Wait for DB to be ready and create tables
    for i in range(10):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(UserBase.metadata.create_all)
                await conn.run_sync(OrgBase.metadata.create_all)
            logger.info("database_initialized", tables_created=["users", "organizations", "user_organization"])
            break
        except OperationalError as e:
            logger.warning("database_connection_retry", attempt=i+1, max_attempts=10, error=str(e))
            await asyncio.sleep(2)
    else:
        logger.error("database_connection_failed", message="Failed to connect to database after 10 attempts")
        raise RuntimeError("Failed to connect to database after 10 attempts") from None

    # ✅ MARK AS READY AFTER STARTUP TASKS
    app.state.ready = True
    yield

    # Shutdown
    app.state.ready = False
    await engine.dispose()
    logger.info("application_shutdown", message="Database engine disposed")

"""


"""


# src/omniai/api/v1/schemas.py
import re
from typing import List
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr = Field(
        ...,
        description="User's email address. Must be unique across the platform.",
        example="user@example.com"
    )
    password: str = Field(
        ...,
        description=(
            "Secure password with at least 8 characters, including uppercase, "
            "lowercase, digit, and special character."
        ),
        min_length=8,
        example="MyP@ssw0rd!"
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain an uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain a lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain a digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain a special character")
        return v


class Token(BaseModel):
    access_token: str = Field(
        ...,
        description="JWT access token for authenticating API requests",
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer' for this API)",
        example="bearer"
    )


class OrganizationSummary(BaseModel):
    id: str = Field(
        ...,
        description="Unique organization ID (org_... format)",
        example="org_a1b2c3d4e5f6"
    )
    name: str = Field(
        ...,
        description="Human-readable organization name",
        example="Acme Corp"
    )
    slug: str = Field(
        ...,
        description="URL-friendly organization identifier",
        example="acme-corp"
    )
    role: str = Field(
        ...,
        description="User's role in this organization: 'owner' or 'member'",
        example="owner"
    )
    is_default: bool = Field(
        ...,
        description="Whether this is the user's default organization on login",
        example=True
    )


class UserMe(BaseModel):
    id: str = Field(
        ...,
        description="Unique user ID (usr_... format)",
        example="usr_x9y8z7w6v5u4"
    )
    email: str = Field(
        ...,
        description="User's verified email address",
        example="user@example.com"
    )
    active_organization_id: str = Field(
        ...,
        description="ID of the currently active organization",
        example="org_a1b2c3d4e5f6"
    )
    role_in_active_org: str = Field(
        ...,
        description="User's role in the active organization",
        example="admin"
    )
    organizations: List[OrganizationSummary] = Field(
        ...,
        description="List of all organizations the user belongs to"
    )


    """


###############################################################
# Unit tests for src/omniai/services/invite.py
###############################################################

"""
@pytest.mark.asyncio
async def test_create_invite_success(db):
    from omniai.services.invite import create_invite
    from omniai.api.v1.schemas import InviteCreate
    from omniai.services.organization import create_organization_for_user
    from omniai.services.auth import create_user_with_org
    #from omniai.models.user import User
    from sqlalchemy import select

    # Generate unique emails
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    invitee_email = f"invitee_{uuid.uuid4().hex}@test.com"

    # Create owner
    await create_user_with_org(db, owner_email, "SecurePass123!")
    result = await db.execute(select(User).where(User.email == owner_email))
    owner = result.scalar_one()
    
    # Create org
    org = await create_organization_for_user(db, owner.id, "Test Org", set_as_default=False)
    await db.commit()

    # Create invite
    invite_data = InviteCreate(email=invitee_email)
    invite = await create_invite(db, org.id, owner.id, invite_data)

    assert invite.email == invitee_email
    assert invite.organization_id == org.id
    assert invite.invited_by_id == owner.id
    assert len(invite.token) > 20


@pytest.mark.asyncio
async def test_create_invite_forbidden_not_owner(db):
    from omniai.services.invite import create_invite
    from omniai.api.v1.schemas import InviteCreate
    from omniai.services.organization import create_organization_for_user
    from omniai.services.auth import create_user_with_org
    #from omniai.models.user import User
    from sqlalchemy import select

    # Unique emails
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    non_owner_email = f"nonowner_{uuid.uuid4().hex}@test.com"

    # Create two users
    await create_user_with_org(db, owner_email, "SecurePass123!")
    await create_user_with_org(db, non_owner_email, "SecurePass123!")
    
    # Get users
    owner_result = await db.execute(select(User).where(User.email == owner_email))
    owner = owner_result.scalar_one()
    non_owner_result = await db.execute(select(User).where(User.email == non_owner_email))
    non_owner = non_owner_result.scalar_one()
    
    # Create org (owned by owner)
    org = await create_organization_for_user(db, owner.id, "Test Org", set_as_default=False)
    await db.commit()

    # Non-owner tries to invite → should fail
    invite_data = InviteCreate(email="newuser@example.com")
    with pytest.raises(HTTPException) as exc:
        await create_invite(db, org.id, non_owner.id, invite_data)
    
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_accept_invite_success(db):
    from omniai.services.invite import create_invite, accept_invite
    from omniai.api.v1.schemas import InviteCreate
    from omniai.services.organization import create_organization_for_user
    from omniai.services.auth import create_user_with_org
    #from omniai.models.user import User
    from sqlalchemy import select

    # Unique emails
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    member_email = f"member_{uuid.uuid4().hex}@test.com"

    # Create owner and org
    await create_user_with_org(db, owner_email, "SecurePass123!")
    owner_result = await db.execute(select(User).where(User.email == owner_email))
    owner = owner_result.scalar_one()
    org = await create_organization_for_user(db, owner.id, "Test Org", set_as_default=False)
    await db.commit()

    # Create invite
    invite_data = InviteCreate(email=member_email)
    invite = await create_invite(db, org.id, owner.id, invite_data)
    await db.commit()

    # Create member user
    await create_user_with_org(db, member_email, "SecurePass123!")
    member_result = await db.execute(select(User).where(User.email == member_email))
    member = member_result.scalar_one()

    # Accept invite
    await accept_invite(db, invite.token, member.id)

    # Verify membership
    from omniai.models.user import user_organization
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
    from omniai.services.invite import accept_invite
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await accept_invite(db, "invalid-token", "usr_123")
    
    assert exc.value.status_code == 400

"""


###############################################################
# Unit tests for src/omniai/services/invite.py
###############################################################

"""
@pytest.mark.asyncio
async def test_create_invite_success(db):
    from omniai.services.invite import create_invite
    from omniai.api.v1.schemas import InviteCreate
    from omniai.services.organization import create_organization_for_user
    from omniai.models.user import user_organization
    #from omniai.models.user import User
    #from omniai.models.organization import Organization
    #from sqlalchemy import select

    # --- INLINE NO-COMMIT USER CREATION ---
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    hashed_pw = get_password_hash("SecurePass123!")
    owner = User(email=owner_email, hashed_password=hashed_pw)
    db.add(owner)
    await db.flush()

    personal_org = Organization(
        name=f"Personal – {owner_email}",
        slug=f"personal-{owner_email.replace('@', '').replace('.', '')}"
    )
    db.add(personal_org)
    await db.flush()
   
    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=personal_org.id,
            role="owner",
            is_default=True
        )
    )
    # --- END INLINE ---

    # Create org
    org = await create_organization_for_user(db, owner.id, "Test Org", set_as_default=False)
    # ⚠️ Do NOT commit — keep in transaction

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
    from omniai.services.invite import create_invite
    from omniai.api.v1.schemas import InviteCreate
    from omniai.services.organization import create_organization_for_user
    #from omniai.models.user import User
    #from omniai.models.organization import Organization
    from sqlalchemy import select

    # --- OWNER (no commit) ---
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    owner = User(email=owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner)
    await db.flush()
    # Skip personal org — not needed for this test

    # --- NON-OWNER (no commit) ---
    non_owner_email = f"nonowner_{uuid.uuid4().hex}@test.com"
    non_owner = User(email=non_owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(non_owner)
    await db.flush()

    # Create org (owned by owner)
    org = await create_organization_for_user(db, owner.id, "Test Org", set_as_default=False)

    # Non-owner tries to invite → should fail
    invite_data = InviteCreate(email="newuser@example.com")
    with pytest.raises(HTTPException) as exc:
        await create_invite(db, org.id, non_owner.id, invite_data)
    
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_accept_invite_success(db):
    from omniai.services.invite import create_invite, accept_invite
    from omniai.api.v1.schemas import InviteCreate
    from omniai.services.organization import create_organization_for_user
    #from omniai.models.user import User
    #from omniai.models.organization import Organization
    from sqlalchemy import select

    # --- OWNER (no commit) ---
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    owner = User(email=owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner)
    await db.flush()

    # Create org
    org = await create_organization_for_user(db, owner.id, "Test Org", set_as_default=False)

    # --- MEMBER (no commit) ---
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
    from omniai.models.user import user_organization
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
    from omniai.services.invite import accept_invite
    #from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await accept_invite(db, "invalid-token", "usr_123")
    
    assert exc.value.status_code == 400

"""




#############################################################################################


"""
@pytest.mark.asyncio
async def test_create_invite_success(db):
    #from omniai.services.invite import create_invite
    #from omniai.api.v1.schemas import InviteCreate
    #from omniai.models.user import User, user_organization
    #from omniai.models.organization import Organization
    #from sqlalchemy import select
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
    #from omniai.services.invite import create_invite
    #from omniai.api.v1.schemas import InviteCreate
    #from omniai.models.user import User, user_organization
    #from omniai.models.organization import Organization
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
    #from omniai.services.invite import create_invite, accept_invite
    #from omniai.api.v1.schemas import InviteCreate
    #from omniai.models.user import User, user_organization
    #from omniai.models.organization import Organization
    #from sqlalchemy import select
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
    #from omniai.services.invite import accept_invite
    #from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await accept_invite(db, "invalid-token", "usr_123")
    
    assert exc.value.status_code == 400
"""



"""
@pytest.mark.asyncio
async def test_get_user_from_token_missing_sub():
    # Mock: db.execute returns a result that .scalar_one_or_none() → None
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute = AsyncMock(return_value=mock_result)  # ✅ FIXED

    # Patch decode_token to return dict without "sub"
    with patch("omniai.core.jwt.decode_token", return_value={"exp": 1769757322}):
        user = await get_user_from_token(mock_db, "valid-token")
        assert user is None
        # Covers: invalid/missing sub path

        
        
@pytest.mark.asyncio
async def test_get_user_from_token_user_not_found():
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Patch decode_token to return a valid-looking user ID
    with patch("omniai.core.jwt.decode_token", return_value={"sub": "usr_123"}):
        user = await get_user_from_token(mock_db, "valid-token")

    # Correct assertion: function fails safely
    assert user is None
"""
