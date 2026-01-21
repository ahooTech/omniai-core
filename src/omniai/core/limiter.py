
import os
from functools import wraps
from typing import Any, Callable, Coroutine, Optional, TypeVar, cast

from slowapi import Limiter
from starlette.requests import Request

# ✅ Custom key function that respects X-Forwarded-For
def get_real_client_ip(request: Request) -> str:
    # Check X-Forwarded-For first (Render, Cloudflare, etc.)
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # X-Forwarded-For: client, proxy1, proxy2
        return forwarded.split(",")[0].strip()
    # Fallback to direct remote address
    return request.client.host if request.client else "127.0.0.1"

DISABLE_RATE_LIMIT = os.getenv("OMNIAI_DISABLE_RATE_LIMIT", "0").lower() in ("1", "true", "yes")
REDIS_URL = os.getenv("REDIS_URL")

_real_limiter: Optional[Limiter] = None

if not DISABLE_RATE_LIMIT:
    if REDIS_URL:
        _real_limiter = Limiter(
            key_func=get_real_client_ip,  # ← Use real IP
            storage_uri=REDIS_URL
        )
    else:
        _real_limiter = Limiter(key_func=get_real_client_ip)

F = TypeVar("F", bound=Callable[..., Coroutine[Any, Any, Any]])

def conditional_limit(limit: str) -> Callable[[F], F]:
    if DISABLE_RATE_LIMIT or _real_limiter is None:
        def decorator(func: F) -> F:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                return await func(*args, **kwargs)
            return cast(F, wrapper)
        return decorator
    else:
        return _real_limiter.limit(limit)

limiter = _real_limiter