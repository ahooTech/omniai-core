import pytest
from httpx import AsyncClient
from omniai.main import app

@pytest.mark.asyncio
async def test_missing_tenant_id():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/v1/users/me")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MISSING_TENANT_ID"

@pytest.mark.asyncio
async def test_invalid_tenant_id():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/v1/users/me", headers={"x-tenant-id": ""})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_TENANT_ID"