
# Override database? For now, we'll use the real one in dev (you'll improve this later)
"""
import pytest
from httpx import AsyncClient, ASGITransport
from omniai.main import app

from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import text
from omniai.main import app
from omniai.core.config import settings
from omniai.db.session import get_db  # for override
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from omniai.models.user import Base as UserBase
from omniai.models.organization import Base as OrgBase

# --- Create a test-only engine ---
test_engine = create_async_engine(
    settings.DATABASE_URL,  # loaded from .env.test.docker → omniai_test
    poolclass=NullPool,     # critical for test isolation
    echo=False,
)

TestSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

# --- Create tables before all tests ---
@pytest.fixture(scope="session", autouse=True)
async def create_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.create_all)
        await conn.run_sync(OrgBase.metadata.create_all)
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
    yield
    # Optionally: drop tables (not needed since you drop DB in docker-compose)

# --- Override get_db to use test engine ---
async def get_test_db():
    async with TestSessionLocal() as session:
        yield session

# --- Your tests ---


# Your existing tests below — no changes needed

@pytest.mark.asyncio
async def test_health_check():
    # Use ASGITransport to wrap the FastAPI app
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        response = await ac.get("/v1/health")  # or any route
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "service": "omniai-core"}


@pytest.mark.asyncio
async def test_full_auth_flow_with_default_tenant():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        # --- Step 1: Signup ---
        email = "integration.test@omniai.dev"
        password = "SecurePass123!"
        signup_response = await ac.post(
            "/v1/auth/signup",
            json={"email": email, "password": password}
        )
        assert signup_response.status_code == 201

        # --- Step 2: Login (only get token) ---
        login_response = await ac.post(
            "/v1/auth/login",
            data={"username": email, "password": password},  # OAuth2PasswordRequestForm uses 'username'
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # --- Step 3: Call /v1/me WITHOUT X-Tenant-ID → should auto-use DEFAULT org ---
        me_response = await ac.get(
            "/v1/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        user_data = me_response.json()
        assert user_data["email"] == email
        assert "active_organization_id" in user_data
        assert "organizations" in user_data  # this should equal default_org

        assert isinstance(user_data["active_organization_id"], str)
        default_org_id = user_data["active_organization_id"]

        # --- Step 4: Call /v1/me WITH X-Tenant-ID = default org → should work ---
        me_response2 = await ac.get(
            "/v1/me",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": default_org_id
            }
        )
        assert me_response2.status_code == 200

        # --- Step 5: (Optional) Verify user only has 1 org (default) at signup ---
        assert len(user_data["organizations"]) >= 1
        org_ids = [org["id"] for org in user_data["organizations"]]
        assert default_org_id in org_ids



@pytest.mark.asyncio
async def test_user_cannot_access_other_tenant():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create User A in Org A
        email_a = "usera@test.com"
        await ac.post("/v1/auth/signup", json={"email": email_a, "password": "Pass123!"})
        login_a = await ac.post("/v1/auth/login", data={"username": email_a, "password": "Pass123!"})
        token_a = login_a.json()["access_token"]

        # Get User A's default org
        me_a = await ac.get("/v1/me", headers={"Authorization": f"Bearer {token_a}"})
        org_a_id = me_a.json()["active_organization_id"]

        # Create User B in Org B
        email_b = "userb@test.com"
        await ac.post("/v1/auth/signup", json={"email": email_b, "password": "Pass123!"})
        login_b = await ac.post("/v1/auth/login", data={"username": email_b, "password": "Pass123!"})
        token_b = login_b.json()["access_token"]

        me_b = await ac.get("/v1/me", headers={"Authorization": f"Bearer {token_b}"})
        org_b_id = me_b.json()["active_organization_id"]

        # Now: User A tries to access Org B → should fail
        response = await ac.get(
            "/v1/me",
            headers={
                "Authorization": f"Bearer {token_a}",
                "X-Tenant-ID": org_b_id  # ❌ Not User A's org!
            }
        )
        assert response.status_code == 403
"""

"""
from omniai.core.config import settings
# Create test tables once before all tests
@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    async def _setup():
        # Use the same DB URL as the app
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        from omniai.models.user import Base as UserBase
        from omniai.models.organization import Base as OrgBase
        async with engine.begin() as conn:
            await conn.run_sync(UserBase.metadata.create_all)
            await conn.run_sync(OrgBase.metadata.create_all)
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
        await engine.dispose()
    asyncio.run(_setup())

"""

# tests/unit/test_auth.py
import pytest
import httpx

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
        await ac.post("/v1/auth/signup", json={"email": "usera@test.com", "password": "Pass123!"})
        login_a = await ac.post("/v1/auth/login", data={"username": "usera@test.com", "password": "Pass123!"})
        token_a = login_a.json()["access_token"]
        me_a = await ac.get("/v1/me", headers={"Authorization": f"Bearer {token_a}"})
        org_a = me_a.json()["active_organization_id"]

        # User B
        await ac.post("/v1/auth/signup", json={"email": "userb@test.com", "password": "Pass123!"})
        login_b = await ac.post("/v1/auth/login", data={"username": "userb@test.com", "password": "Pass123!"})
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
        await ac.post("/v1/auth/signup", json={"email": email, "password": "Pass123!"})
        r2 = await ac.post("/v1/auth/signup", json={"email": email, "password": "AnotherPass!"})
        assert r2.status_code == 400
        assert "email already registered" in r2.json()["detail"].lower()



# Fake tenant ID 8
@pytest.mark.asyncio
async def test_access_nonexistent_organization():
    async with httpx.AsyncClient(base_url=BASE_URL) as ac:
        # Signup + login
        email = "nonexist@test.com"
        await ac.post("/v1/auth/signup", json={"email": email, "password": "Pass123!"})
        login = await ac.post("/v1/auth/login", data={"username": email, "password": "Pass123!"})
        token = login.json()["access_token"]

        # Try to access a fake org UUID
        fake_org_id = "12345678-1234-5678-1234-567812345678"
        resp = await ac.get(
            "/v1/me",
            headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": fake_org_id}
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "ORG_NOT_FOUND"



# tests if token format is checked 9
def test_decode_invalid_token():
    from jose import JWTError
    try:
        decode_token("invalid.token.here")
        assert False, "Should have raised JWTError"
    except JWTError:
        pass  # Expected


# tests if token can be created and decoded 10
from omniai.core.jwt import create_access_token, decode_token
def test_jwt_roundtrip():
    user_id = "usr_123abc"
    token = create_access_token({"sub": user_id})
    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert "exp" in payload


# User signed up an no default org was created,  then they login and when /me is fetched it finds no default org. #Should never happen 11
@pytest.mark.asyncio
async def test_user_with_no_default_org_fails_gracefully():
    async with httpx.AsyncClient(base_url=BASE_URL) as ac:
        email = "nodefault@test.com"
        password = "Pass123!"

        await ac.post("/v1/auth/signup", json={"email": email, "password": password})
        login = await ac.post("/v1/auth/login", data={"username": email, "password": password})
        token = login.json()["access_token"]

        from omniai.db.session import AsyncSessionLocal
        from omniai.models.user import User, user_organization
        from omniai.models.organization import Organization
        from sqlalchemy import delete, select

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
from omniai.services.auth import get_password_hash, verify_password
def test_password_hashing():
    pwd = "TestPass123!"
    hashed = get_password_hash(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("Wrong", hashed) is False


"""
# Password strength test 13
@pytest.mark.asyncio
async def test_signup_weak_password():
    async with httpx.AsyncClient(base_url=BASE_URL) as ac:
        r = await ac.post("/v1/auth/signup", json={"email": "weak@test.com", "password": "123"})
        assert r.status_code == 422
        assert "Password must be at least 8 characters" in r.json()["detail"][0]["msg"]

"""


