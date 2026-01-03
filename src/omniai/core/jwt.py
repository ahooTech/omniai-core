from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt import PyJWTError

from omniai.core.config import settings


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": True, "require": ["exp", "sub"]},
        )
        user_id = payload.get("sub")
        if not isinstance(user_id, str) or not user_id.startswith("usr_"):
            raise PyJWTError("Invalid user ID format")
        return payload
    except PyJWTError as e:
        raise PyJWTError(f"Token decode failed: {str(e)}") from e
