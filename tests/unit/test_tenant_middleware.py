"""
Unit Tests for TenantValidationMiddleware

These tests will evolve through Phase 1 as follows:

✅ [DONE] 1. Basic validation
   - Missing X-Tenant-ID → 400 MISSING_TENANT_ID
   - Empty string → 400 INVALID_TENANT_ID

🔜 [PHASE 1: Security & Hardening]
   - Test malicious inputs:
       • Extremely long tenant ID (DoS protection)
       • Non-UTF-8 headers (security boundary)
       • Header with path traversal chars (e.g., "../../")
   - Verify no information leakage in error messages

🔜 [PHASE 1: Backend Engineering]
   - Add test for valid tenant ID format (e.g., UUID vs slug)
   - Test case sensitivity (if applicable)

🔜 [PHASE 1: Database Engineering]
   - Once Organization model exists:
       • Valid ID but non-existent tenant → 404 TENANT_NOT_FOUND
       • Valid ID and existing tenant → request proceeds
   - Test DB connection failure handling (middleware resilience)

🔜 [PHASE 1: Observability]
   - Verify structured logs are emitted on validation failure
   - Ensure metrics counters increment on errors

🔜 [PHASE 1: System Architecture]
   - Test middleware ordering (e.g., runs before auth, after CORS)
   - Test idempotency: repeated calls don’t mutate state

🔜 [PHASE 1: Engineering Mindset]
   - Add parametrized tests for 10+ invalid formats
   - Achieve 100% branch coverage (including edge cases)
   - Add integration test with real HTTP client + DB

🔜 [PHASE 2+]
   - Test tenant-aware AI routing (e.g., tenant-specific model selection)
   - Validate multi-tenancy in agent workflows

PRINCIPLES:
- Every error code must have a test
- Every guard clause must be exercised
- No test should depend on external state (mock DB when needed)
- Tests must run in <100ms (unit, not integration)
"""


import pytest
from httpx import AsyncClient, ASGITransport
from omniai.main import app
# include pip install httpx in my pyproject.toml
@pytest.mark.asyncio
async def test_missing_tenant_id():
    # Use ASGITransport to wrap the FastAPI app
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        response = await ac.get("/v1/agriculture")  # or any route
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MISSING_TENANT_ID"

@pytest.mark.asyncio
async def test_invalid_tenant_id():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        response = await ac.get("/v1/agriculture", headers={"x-tenant-id": ""})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_TENANT_ID"