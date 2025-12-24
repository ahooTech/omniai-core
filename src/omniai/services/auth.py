# src/omniai/services/auth.py
import re
from datetime import datetime, timedelta
from sqlalchemy import select, insert
from passlib.context import CryptContext
from jose import jwt
from omniai.core.config import settings
from omniai.models.user import User, user_organization
from omniai.models.organization import Organization
from sqlalchemy.ext.asyncio import AsyncSession
import bcrypt

# src/omniai/services/auth.py
def get_password_hash(password: str) -> str:
    # ✅ Truncate to 72 bytes (bcrypt limit)
    password_bytes = password.encode("utf-8")
    truncated = password_bytes[:72]
    # Hash using bcrypt
    hashed = bcrypt.hashpw(truncated, bcrypt.gensalt())
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    plain_bytes = plain_password.encode("utf-8")[:72]
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(plain_bytes, hashed_bytes)

"""
# TEMPORARY: for development only
import hashlib

def get_password_hash(password: str) -> str:
    # ⚠️ NEVER use this in production
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password """

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

"""def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password) """

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

async def authenticate_user(db: AsyncSession, email: str, password: str):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

async def create_user_with_org(db: AsyncSession, email: str, password: str):
    """
    Creates a new user with a Personal organization.
    The user is the OWNER of this org, and it is set as their DEFAULT.
    """
    # === 1. Create Personal Organization ===
    # Later: org_name = f"Personal – {email} ({country_code})"
    # In future, infer from email domain or IP — for now, just label
    personal_org_name = f"Personal – {email}"
    
    # Generate slug
    normalized = re.sub(r"[^a-z0-9\s-]", "", personal_org_name.lower())
    base_slug = re.sub(r"[-\s]+", "-", normalized).strip("-")[:26]
    
    slug = base_slug
    counter = 1
    while True:
        result = await db.execute(select(Organization).where(Organization.slug == slug))
        if result.scalar_one_or_none() is None:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1
        if counter > 100:
            raise ValueError("Could not generate a unique slug for Personal org")

    # Save org
    org = Organization(name=personal_org_name, slug=slug)
    db.add(org)
    await db.flush()  # Get org.id

    # === 2. Create User ===
    hashed_pw = get_password_hash(password)
    user = User(email=email, hashed_password=hashed_pw)
    db.add(user)
    await db.flush()  # Get user.id

    # === 3. Link user to org as OWNER + DEFAULT ===
    await db.execute(
        insert(user_organization),
        [{
            "user_id": user.id,
            "organization_id": org.id,
            "is_default": True,
            "role": "owner"
        }]
    )
    
    await db.commit()
    await db.refresh(user)
    return user