import httpx
import pytest
import os

from unittest import mock
from unittest.mock import AsyncMock, MagicMock, patch

from pydantic import ValidationError
from omniai.core.config import Settings


from sqlalchemy.ext.asyncio import AsyncSession
from omniai.api.deps import get_current_user
from omniai.models.user import User
from omniai.services.auth import get_user_from_token
from omniai.api.v1.schemas import UserCreate, OrganizationCreate
from fastapi import HTTPException




# URL of the real app inside Docker
BASE_URL = "http://app:8000"
HTTPX_TIMEOUT = 30.0


# All tests now use real HTTP
# Health check 1
@pytest.mark.asyncio
async def test_health_check():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=HTTPX_TIMEOUT) as ac:
        response = await ac.get("/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "service": "omniai-core"}

# Signup to login to me 2
@pytest.mark.asyncio
async def test_full_auth_flow_with_default_tenant():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=HTTPX_TIMEOUT) as ac:
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
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=HTTPX_TIMEOUT) as ac:
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
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=HTTPX_TIMEOUT) as ac:
        # Signup
        await ac.post("/v1/auth/signup", json={"email": "badpass@test.com", "password": "GoodPass123!"})
        # Login with wrong password
        r = await ac.post("/v1/auth/login", data={"username": "badpass@test.com", "password": "Wrong123!"})
        assert r.status_code == 401
        assert "incorrect email or password" in r.json()["detail"].lower()


# Testing missing header 5
@pytest.mark.asyncio
async def test_protected_route_without_token():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=HTTPX_TIMEOUT) as ac:
        r = await ac.get("/v1/me")
        assert r.status_code == 401
        assert r.json()["error"]["code"] == "MISSING_AUTH_TOKEN"

# Testing invalid token 6
@pytest.mark.asyncio
async def test_protected_route_with_malformed_token():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=HTTPX_TIMEOUT) as ac:
        r = await ac.get("/v1/me", headers={"Authorization": "Bearer invalid.junk.token"})
        assert r.status_code == 401
        assert r.json()["error"]["code"] == "INVALID_TOKEN"


# Don't allow same email signup twice 7
@pytest.mark.asyncio
async def test_signup_duplicate_email():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=HTTPX_TIMEOUT) as ac:
        email = "dup@test.com"
        await ac.post("/v1/auth/signup", json={"email": email, "password": "SecurePass123!"})
        r2 = await ac.post("/v1/auth/signup", json={"email": email, "password": "AnotherPass123!"})
        assert r2.status_code == 400
        assert "email already registered" in r2.json()["detail"].lower()



# Fake tenant ID 8
@pytest.mark.asyncio
async def test_access_nonexistent_organization():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=HTTPX_TIMEOUT) as ac:
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
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=HTTPX_TIMEOUT) as ac:
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
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=HTTPX_TIMEOUT) as ac:
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


###############################################################
# Unit tests for src/omniai/services/auth.py — error paths in get_user_from_token
###############################################################

@pytest.mark.asyncio
async def test_get_user_from_token_missing_sub():
    mock_db = AsyncMock(spec=AsyncSession)

    with patch("omniai.services.auth.decode_token", return_value={"exp": 123456}):
        user = await get_user_from_token(mock_db, "valid-token")

    assert user is None


@pytest.mark.asyncio
async def test_get_user_from_token_invalid_token():
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute = AsyncMock(return_value=mock_result)  # ✅ FIXED

    # Patch decode_token to raise exception
    with patch("omniai.core.jwt.decode_token", side_effect=Exception("Invalid token")):
        user = await get_user_from_token(mock_db, "invalid-token")
        assert user is None
        # Covers: exception / decode failure path


@pytest.mark.asyncio
async def test_get_user_from_token_user_not_found():
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # sync method

    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("omniai.services.auth.decode_token", return_value={"sub": "usr_123"}):
        user = await get_user_from_token(mock_db, "valid-token")

    assert user is None


@pytest.mark.asyncio
async def test_get_user_from_token_error_paths():
    # Directly test multiple error branches in get_user_from_token

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute = AsyncMock(return_value=mock_result)  # ✅ FIXED

    # Case 1: missing "sub"
    with patch("omniai.core.jwt.decode_token", return_value={"exp": 1769757322}):
        user = await get_user_from_token(mock_db, "valid-token")
        assert user is None

    # Case 2: decode exception
    with patch("omniai.core.jwt.decode_token", side_effect=Exception("Decode fail")):
        user = await get_user_from_token(mock_db, "invalid-token")
        assert user is None

    # Case 3: user not found (DB query returns None)
    with patch("omniai.core.jwt.decode_token", return_value={"sub": "usr_123"}):
        user = await get_user_from_token(mock_db, "valid-token")
        assert user is None


@pytest.mark.asyncio
async def test_get_user_from_token_decode_returns_non_dict():
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute = AsyncMock(return_value=mock_result)  # ✅ FIXED

    # Patch decode_token to return a non-dict (AttributeError on .get)
    with patch("omniai.core.jwt.decode_token", return_value="invalid"):
        user = await get_user_from_token(mock_db, "valid-token")
        assert user is None



###############################################################
# Unit tests for src/omniai/api/deps.py
###############################################################


class MockCredentials:
    def __init__(self, credentials: str):
        self.credentials = credentials

class MockDB:
    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass


@pytest.mark.asyncio
async def test_get_current_user_success():
    from sqlalchemy.ext.asyncio import AsyncSession
    
    with patch("omniai.api.deps.get_user_from_token", new_callable=AsyncMock) as mock_func:
        mock_func.return_value = User(id="usr_123", email="test@example.com", hashed_password="x")
        mock_db = AsyncMock(spec=AsyncSession)
        
        user = await get_current_user(
            credentials=MockCredentials("valid-token"),
            db=mock_db
        )
        assert user.id == "usr_123"
        mock_func.assert_called_once_with(mock_db, "valid-token")


@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    with patch("omniai.api.deps.get_user_from_token", new_callable=AsyncMock) as mock_func:
        mock_func.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            await get_current_user(
                credentials=MockCredentials("invalid-token"),
                db=MockDB()
            )
        assert exc.value.status_code == 401



###############################################################
# Unit tests for src/omniai/api/v1/schemas.py
###############################################################

def test_user_create_password_validation():

    # Valid password
    valid = UserCreate(email="test@example.com", password="SecurePass123!")
    assert valid.password == "SecurePass123!"

    # Invalid passwords
    with pytest.raises(ValueError, match="Password must be at least 8 characters"):
        UserCreate(email="test@example.com", password="Short1!")

    with pytest.raises(ValueError, match="Password must contain an uppercase letter"):
        UserCreate(email="test@example.com", password="nopassword123!")

    with pytest.raises(ValueError, match="Password must contain a lowercase letter"):
        UserCreate(email="test@example.com", password="NOPASSWORD123!")

    with pytest.raises(ValueError, match="Password must contain a digit"):
        UserCreate(email="test@example.com", password="NoDigitsHere!")

    with pytest.raises(ValueError, match="Password must contain a special character"):
        UserCreate(email="test@example.com", password="NoSpecial123")


def test_organization_create_name_validation():

    # Valid name
    valid = OrganizationCreate(name="My Org")
    assert valid.name == "My Org"

    # Empty name
    with pytest.raises(ValueError, match="Organization name cannot be empty"):
        OrganizationCreate(name="   ")

    # Too long
    with pytest.raises(ValueError, match="Organization name too long"):
        OrganizationCreate(name="A" * 101)