# src/omniai/services/auth.py
import re
from datetime import datetime, timedelta
from sqlalchemy import select
from passlib.context import CryptContext
from jose import jwt
from omniai.core.config import settings
from omniai.models.user import User
from omniai.models.organization import Organization
from sqlalchemy.ext.asyncio import AsyncSession

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_slug(name: str) -> str:
    """Generate a URL-safe, unique-friendly slug from organization name."""
    # Convert to lowercase and keep only alphanumeric, spaces, and hyphens
    normalized = re.sub(r"[^a-z0-9\s-]", "", name.lower())
    # Replace any sequence of spaces or hyphens with a single hyphen
    slug = re.sub(r"[-\s]+", "-", normalized).strip("-")
    # Truncate to 26 chars to allow room for suffix (e.g., '-1')
    return slug[:26]

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

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


async def create_user_with_org(db: AsyncSession, email: str, password: str, org_name: str):
    # later admin should be able to create organization and sent invite links via email.
    
    base_slug = generate_slug(org_name)
    slug = base_slug
    counter = 1

    # Ensure slug is unique across all organizations
    while True:
        result = await db.execute(select(Organization).where(Organization.slug == slug))
        if result.scalar_one_or_none() is None:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1
        if counter > 100:
            raise ValueError("Could not generate a unique slug after 100 attempts")

    # Create organization with slug
    org = Organization(name=org_name, slug=slug)
    db.add(org)
    await db.flush()  # Populate org.id

    # Create user
    hashed_pw = get_password_hash(password)
    user = User(email=email, hashed_password=hashed_pw, organization_id=org.id)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user