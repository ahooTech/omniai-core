# src/omniai/api/v1/me.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select  # ← 🔴 WAS MISSING — NOW ADDED
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from omniai.core.config import settings
from omniai.db.session import get_db
from omniai.models.user import User
from omniai.api.v1.schemas import UserMe

router = APIRouter()

# OAuth2 Bearer token dependency
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth/login")

async def get_current_user(db: AsyncSession, token: str):
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        email: str = payload.get("sub")
        tenant_id: str = payload.get("tenant")
        if email is None or tenant_id is None:
            raise JWTError
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or user.organization_id != tenant_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

@router.get("/me", response_model=UserMe)
async def read_users_me(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
):
    user = await get_current_user(db, token)
    return user