"""
# In your health router file (e.g., src/omniai/api/v1/health.py or similar)

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from omniai.db.session import get_db  # ← adjust import to match your project


class HealthResponse(BaseModel):
    status: str
    service: str


router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="omniai-core")


@router.get("/health/ready", response_model=HealthResponse)
async def health_ready(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    try:
        await db.execute(text("SELECT 1"))
        return HealthResponse(status="ready", service="omniai-core")
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database unavailable") from None
"""

from fastapi import APIRouter, HTTPException, Depends, Request  # ← ADD Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from omniai.db.session import get_db


class HealthResponse(BaseModel):
    status: str
    service: str


router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="omniai-core")


@router.get("/health/ready", response_model=HealthResponse)
async def health_ready(
    request: Request,  # ← ADD THIS
    db: AsyncSession = Depends(get_db)
) -> HealthResponse:
    # ✅ Check if app has finished startup
    if not getattr(request.app.state, 'ready', False):
        raise HTTPException(status_code=503, detail="Startup incomplete") from None

    # ✅ Check DB connectivity
    try:
        await db.execute(text("SELECT 1"))
        return HealthResponse(status="ready", service="omniai-core")
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database unavailable") from None