
import httpx
import pytest
import os

from unittest import mock
from pydantic import ValidationError
from omniai.core.config import Settings
from typing import AsyncGenerator


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
    """Create all tables once."""
    from omniai.models.user import Base as UserBase
    from omniai.models.organization import Base as OrgBase
    async with _test_engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.create_all)
        await conn.run_sync(OrgBase.metadata.create_all)

# Initialize DB once at module level
asyncio.run(_init_test_db())
# --- END TEST DB SETUP ---

#############################################################################################################




# URL of the real app inside Docker
BASE_URL = "http://app:8000"


# All tests now use real HTTP
# Health check 1
@pytest.mark.asyncio
async def test_health_check():
    async with httpx.AsyncClient(base_url=BASE_URL) as ac:
        response = await ac.get("/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "service": "omniai-core"}

# Signup to login to me 2
@pytest.mark.asyncio
async def test_full_auth_flow_with_default_tenant():
    async with httpx.AsyncClient(base_url=BASE_URL) as ac:
        email = "integration4.test@omniai.dev"
        password = "SecurePass123!"
        r1 = await ac.post("/v1/auth/signup", json={"email": email, "password": password})
        assert r1.status_code == 201

        r2 = await ac.post("/v1/auth/login", data={"username": email, "password": password})
        assert r2.status_code == 200
        token = r2.json()["access_token"]

        r3 = await ac.get("/v1/me", headers={"Authorization": f"Bearer {token}"})
        assert r3.status_code == 200
        data = r3.json()
        assert data["email"] == email
        assert "active_organization_id" in data

        org_id = data["active_organization_id"]
        r4 = await ac.get("/v1/me", headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": org_id})
        assert r4.status_code == 200

# Token accessing another token's tenant 3
@pytest.mark.asyncio
async def test_user_cannot_access_other_tenant():
    async with httpx.AsyncClient(base_url=BASE_URL) as ac:
        # User A
        await ac.post("/v1/auth/signup", json={"email": "usera@test.com", "password": "SecurePass123!"})
        login_a = await ac.post("/v1/auth/login", data={"username": "usera@test.com", "password": "SecurePass123!"})
        token_a = login_a.json()["access_token"]
        #me_a = await ac.get("/v1/me", headers={"Authorization": f"Bearer {token_a}"})
        #org_a = me_a.json()["active_organization_id"]

        # User B
        await ac.post("/v1/auth/signup", json={"email": "userb@test.com", "password": "SecurePass123!"})
        login_b = await ac.post("/v1/auth/login", data={"username": "userb@test.com", "password": "SecurePass123!"})
        token_b = login_b.json()["access_token"]
        me_b = await ac.get("/v1/me", headers={"Authorization": f"Bearer {token_b}"})
        org_b = me_b.json()["active_organization_id"]

        # User A tries to access Org B → should be 403
        resp = await ac.get(
            "/v1/me",
            headers={"Authorization": f"Bearer {token_a}", "X-Tenant-ID": org_b}
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "NOT_ORG_MEMBER"




# Loging in with wrong password 4
@pytest.mark.asyncio
async def test_login_with_wrong_password():
    async with httpx.AsyncClient(base_url=BASE_URL) as ac:
        # Signup
        await ac.post("/v1/auth/signup", json={"email": "badpass@test.com", "password": "GoodPass123!"})
        # Login with wrong password
        r = await ac.post("/v1/auth/login", data={"username": "badpass@test.com", "password": "Wrong123!"})
        assert r.status_code == 401
        assert "incorrect email or password" in r.json()["detail"].lower()


# Testing missing header 5
@pytest.mark.asyncio
async def test_protected_route_without_token():
    async with httpx.AsyncClient(base_url=BASE_URL) as ac:
        r = await ac.get("/v1/me")
        assert r.status_code == 401
        assert r.json()["error"]["code"] == "MISSING_AUTH_TOKEN"

# Testing invalid token 6
@pytest.mark.asyncio
async def test_protected_route_with_malformed_token():
    async with httpx.AsyncClient(base_url=BASE_URL) as ac:
        r = await ac.get("/v1/me", headers={"Authorization": "Bearer invalid.junk.token"})
        assert r.status_code == 401
        assert r.json()["error"]["code"] == "INVALID_TOKEN"


# Don't allow same email signup twice 7
@pytest.mark.asyncio
async def test_signup_duplicate_email():
    async with httpx.AsyncClient(base_url=BASE_URL) as ac:
        email = "dup@test.com"
        await ac.post("/v1/auth/signup", json={"email": email, "password": "SecurePass123!"})
        r2 = await ac.post("/v1/auth/signup", json={"email": email, "password": "AnotherPass123!"})
        assert r2.status_code == 400
        assert "email already registered" in r2.json()["detail"].lower()



# Fake tenant ID 8
@pytest.mark.asyncio
async def test_access_nonexistent_organization():
    async with httpx.AsyncClient(base_url=BASE_URL) as ac:
        # Signup + login
        email = "nonexist@test.com"
        await ac.post("/v1/auth/signup", json={"email": email, "password": "SecurePass123!"})
        login = await ac.post("/v1/auth/login", data={"username": email, "password": "SecurePass123!"})
        token = login.json()["access_token"]

        # Try to access a fake org UUID
        fake_org_id = "12345678-1234-5678-1234-567812345678"
        resp = await ac.get(
            "/v1/me",
            headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": fake_org_id}
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "ORG_NOT_FOUND"


# tests if token can be created and decoded 10
def test_jwt_roundtrip():
    from omniai.core.jwt import create_access_token, decode_token
    user_id = "usr_123abc"
    token = create_access_token({"sub": user_id})
    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert "exp" in payload

# tests if token format is checked 9
def test_decode_invalid_token():
    from jwt import PyJWTError

    from omniai.core.jwt import decode_token
    try:
        decode_token("invalid.token.here")
        raise AssertionError("Should have raised JWTError")
    except PyJWTError:
        pass  # Expected

# test if token doesn't start with usr_ or isn't an instance of (user_id, str)
def test_decode_token_with_invalid_user_id_format():
    """decode_token should raise PyJWTError if sub is not a valid user ID."""
    from omniai.core.jwt import create_access_token, decode_token
    from jwt import PyJWTError

    # Create token with invalid user ID (doesn't start with "usr_")
    token = create_access_token({"sub": "invalid-user-id"})

    with pytest.raises(PyJWTError) as exc_info:
        decode_token(token)

    assert "Invalid user ID format" in str(exc_info.value)


# User signed up an no default org was created,  then they login and when /me is fetched it finds no default org. #Should never happen 11
@pytest.mark.asyncio
async def test_user_with_no_default_org_fails_gracefully():
    async with httpx.AsyncClient(base_url=BASE_URL) as ac:
        email = "nodefault@test.com"
        password = "SecurePass123!"

        await ac.post("/v1/auth/signup", json={"email": email, "password": password})
        login = await ac.post("/v1/auth/login", data={"username": email, "password": password})
        token = login.json()["access_token"]

        from sqlalchemy import delete, select

        from omniai.db.session import AsyncSessionLocal
        from omniai.models.organization import Organization
        from omniai.models.user import User, user_organization

        async with AsyncSessionLocal() as db:
            user_result = await db.execute(select(User.id).where(User.email == email))
            user_id = user_result.scalar()

            # ✅ FIX: Use hyphen "-", not en dash "–"
            org_name = f"Personal – {email}"
            org_result = await db.execute(select(Organization.id).where(Organization.name == org_name))
            org_id = org_result.scalar()

            if user_id and org_id:
                await db.execute(
                    delete(user_organization)
                    .where(
                        user_organization.c.user_id == user_id,
                        user_organization.c.organization_id == org_id
                    )
                )
                await db.commit()

        resp = await ac.get("/v1/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "NO_DEFAULT_ORG"



# Test password hashing 12
def test_password_hashing():
    from omniai.services.auth import get_password_hash, verify_password
    pwd = "TestPass123!"
    hashed = get_password_hash(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("Wrong", hashed) is False


# Password strength test 13
@pytest.mark.asyncio
async def test_signup_weak_password():
    async with httpx.AsyncClient(base_url=BASE_URL) as ac:
        r = await ac.post("/v1/auth/signup", json={"email": "weak@test.com", "password": "123"})
        assert r.status_code == 422
        assert "Password must be at least 8 characters" in r.json()["detail"][0]["msg"]


# Test JWT_SECRET_KEY exists and valid hence success
def test_settings_loads_with_valid_env():
    """Settings should load successfully when all required env vars are set."""
    with mock.patch.dict(os.environ, {
        "JWT_SECRET_KEY": "test-secret-key",
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost/testdb"
    }, clear=True):
        settings = Settings()
        assert settings.JWT_SECRET_KEY == "test-secret-key"
        assert "testdb" in settings.DATABASE_URL


# Test is missing JWT_SECRET_KEY raises an error
def test_settings_fails_without_jwt_secret_key():
    """Settings must require JWT_SECRET_KEY."""
    # Temporarily remove JWT_SECRET_KEY from environment
    with mock.patch.dict(os.environ, {}, clear=True):
        # Ensure no default is used
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        # Verify the error is about JWT_SECRET_KEY
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("JWT_SECRET_KEY",)
        assert "Field required" in errors[0]["msg"]


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
    from unittest.mock import AsyncMock, MagicMock

    # Create a mock result that mimics .scalar_one_or_none() returning an org (i.e., collision)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = MagicMock()  # Simulate existing org

    # Mock db.execute to return the mock result WHEN AWAITED
    db.execute = AsyncMock(return_value=mock_result)

    email = "slug-collision@test.com"
    password = "TestPass123!"

    with pytest.raises(ValueError, match="Could not generate a unique slug"):
        await create_user_with_org(db, email, password)

    assert db.execute.call_count == 100



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