
# Override database? For now, we'll use the real one in dev (you'll improve this later)

import pytest
from httpx import AsyncClient, ASGITransport
from omniai.main import app
# include pip install httpx in my pyproject.toml

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

        default_org_id = user_data["active_organization_id"]["id"]

        # --- Step 4: Call /v1/me WITH X-Tenant-ID = default org → should work ---
        me_response2 = await ac.get(
            "/v1/me",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(default_org_id)
            }
        )
        assert me_response2.status_code == 200

        # --- Step 5: (Optional) Verify user only has 1 org (default) at signup ---
        assert len(user_data["organizations"]) >= 1
        org_ids = [org["id"] for org in user_data["organizations"]]
        assert default_org_id in org_ids
