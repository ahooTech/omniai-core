# src/omniai/services/auth.py
import re
import bcrypt
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from omniai.core.logging import logger
from omniai.models.organization import Organization
from omniai.models.user import User, user_organization


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


async def authenticate_user(db: AsyncSession, email: str, password: str):
    logger.debug("authenticate_user_start", email=email)

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        logger.debug("authenticate_user_user_not_found", email=email)
        return False

    is_valid = verify_password(password, user.hashed_password)
    if not is_valid:
        logger.debug("authenticate_user_password_invalid", email=email)
        return False

    logger.debug("authenticate_user_success", user_id=str(user.id), email=email)
    return user

async def create_user_with_org(db: AsyncSession, email: str, password: str):
    """
    Creates a new user with a Personal organization.
    The user is the OWNER of this org, and it is set as their DEFAULT.
    """
    # === 1. Create Personal Organization ===
    # Later: org_name = f"Personal – {email} ({country_code})"
    # In future, infer from email domain or IP — for now, just label
    logger.info("create_user_with_org_start", email=email)
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
            logger.error("create_user_with_org_slug_failure", email=email, base_slug=base_slug)
            raise ValueError("Could not generate a unique slug for Personal org")

    # Save org
    org = Organization(name=personal_org_name, slug=slug)
    db.add(org)
    await db.flush()  # Get org.id
    logger.debug("create_user_with_org_org_created", org_id=str(org.id), slug=slug, email=email)

    # === 2. Create User ===
    hashed_pw = get_password_hash(password)
    user = User(email=email, hashed_password=hashed_pw)
    db.add(user)
    await db.flush()  # Get user.id
    logger.debug("create_user_with_org_user_created", user_id=str(user.id), email=email)

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
    logger.info("create_user_with_org_success", user_id=str(user.id), org_id=str(org.id), email=email)
    return user
