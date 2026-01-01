from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
from omniai.core.config import settings

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta is None:
        # ✅ Use value from config
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)



def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": True, "require": ["exp", "sub"]}
        )
        # Validate user ID format (optional but safe)
        user_id = payload.get("sub")
        if not isinstance(user_id, str) or not user_id.startswith("usr_"):
            raise JWTError("Invalid user ID format")
        return payload
    except JWTError as e:
        raise JWTError(f"Token decode failed: {str(e)}") from e
    