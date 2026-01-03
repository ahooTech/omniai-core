## src/omniai/api/v1/auth.py
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from omniai.api.v1.schemas import Token, UserCreate
from omniai.core.jwt import create_access_token
from omniai.core.logging import logger
from omniai.db.session import get_db
from omniai.models.user import User
from omniai.services.auth import authenticate_user, create_user_with_org

router = APIRouter()

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    logger.info("signup_attempt", email=user.email)

    result = await db.execute(select(User).where(User.email == user.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        logger.warn("signup_failed", email=user.email, reason="email_already_registered")
        raise HTTPException(status_code=400, detail="Email already registered") from None

    try:
        new_user = await create_user_with_org(
            db=db,
            email=user.email,
            password=user.password
        )
        logger.info("signup_success", user_id=str(new_user.id), email=user.email)
        return {"msg": "User created"}
    except Exception as e:
        logger.exception("signup_error", email=user.email, error=str(e))
        raise HTTPException(status_code=500, detail="Signup failed") from None


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Token:
    logger.info("login_attempt", email=form_data.username)

    user: Optional[User] = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warn("login_failed", email=form_data.username, reason="invalid_credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    access_token = create_access_token(data={"sub": str(user.id)})  # ensure str
    logger.info("login_success", user_id=str(user.id), email=user.email)

    return Token(access_token=access_token, token_type="bearer")
