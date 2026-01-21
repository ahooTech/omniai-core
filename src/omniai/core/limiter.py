# omniai/core/limiter.py
"""
import os
from functools import wraps
from typing import Callable, Any, Coroutine, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

# Global flag Check if rate limiting is disabled
DISABLE_RATE_LIMIT = os.getenv("OMNIAI_DISABLE_RATE_LIMIT", "0").lower() in ("1", "true", "yes")


# Get Redis URL (optional — if not set, falls back to in-memory)
REDIS_URL = os.getenv("REDIS_URL")

# Define _real_limiter as a module-level global — conditionally
_real_limiter: Optional[Limiter] = None

if not DISABLE_RATE_LIMIT:
    # Real limiter (only used if enabled) &&
    # Use Redis if available, otherwise in-memory (not recommended for prod)
    storage_uri = REDIS_URL if REDIS_URL else None
    _real_limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=storage_uri  # ← This enables Redis!
    )

def conditional_limit(limit: str) -> Callable[..., Callable[..., Coroutine[Any, Any, Any]]]:
    #Apply rate limit only if OMNIAI_DISABLE_RATE_LIMIT is not set.
    if DISABLE_RATE_LIMIT or _real_limiter is None:
        def decorator(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Coroutine[Any, Any, Any]]:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    else:
        return _real_limiter.limit(limit)

# Expose limiter instance for app integration
limiter = _real_limiter

"""

# src/omniai/core/limiter.py
import os
from functools import wraps
from typing import Callable, Any, Coroutine, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
from redis import asyncio as aioredis
from slowapi.storage.redis_storage import RedisStorage

# Global flag
DISABLE_RATE_LIMIT = os.getenv("OMNIAI_DISABLE_RATE_LIMIT", "0").lower() in ("1", "true", "yes")

# Get Redis URL
REDIS_URL = os.getenv("REDIS_URL")

_real_limiter: Optional[Limiter] = None

if not DISABLE_RATE_LIMIT and REDIS_URL:
    # Parse Redis URL for SSL
    if REDIS_URL.startswith("rediss://"):
        # Convert to redis:// + enable SSL
        redis_url = REDIS_URL.replace("rediss://", "redis://")
        ssl = True
    else:
        redis_url = REDIS_URL
        ssl = False

    # Create Redis connection with SSL if needed
    redis_client = aioredis.from_url(
        redis_url,
        decode_responses=True,
        ssl=ssl,
        ssl_cert_reqs=None  # Allow self-signed certs (for Upstash)
    )

    # Use RedisStorage with custom client
    storage = RedisStorage(redis_client)

    _real_limiter = Limiter(
        key_func=get_remote_address,
        storage=storage  # ← Use custom storage
    )

def conditional_limit(limit: str) -> Callable[..., Callable[..., Coroutine[Any, Any, Any]]]:
    if DISABLE_RATE_LIMIT or _real_limiter is None:
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    else:
        return _real_limiter.limit(limit)

# Expose limiter instance for app integration
limiter = _real_limiter

# small edit