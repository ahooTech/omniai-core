
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