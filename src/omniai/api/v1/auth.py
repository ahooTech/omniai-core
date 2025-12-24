# src/omniai/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from omniai.db.session import get_db
from omniai.services.auth import authenticate_user, create_access_token, create_user_with_org
from omniai.api.v1.schemas import UserCreate, Token
from omniai.models.user import User

router = APIRouter()

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if email exists
    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    
    await create_user_with_org(
        db=db,
        email=user.email,
        password=user.password
    )
    return {"msg": "User created"}

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # ✅ ONLY put user.id in token — NO tenant
    access_token = create_access_token(
        data={"sub": user.id}  # ← user.id, not email!
    )
    return {"access_token": access_token, "token_type": "bearer"}