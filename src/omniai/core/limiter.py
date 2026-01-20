# omniai/core/limiter.py
"""
import os
from slowapi import Limiter
from slowapi.util import get_remote_address

# DISABLE_RATE_LIMIT = os.getenv("TESTING", "0") == "1"
DISABLE_RATE_LIMIT = os.getenv("TESTING", "0").lower() in ("1", "true", "yes")

limiter = Limiter(
    key_func=get_remote_address,
    enabled=not DISABLE_RATE_LIMIT
)
"""
import os
from functools import wraps
from typing import Callable, Any, Coroutine
from slowapi import Limiter
from slowapi.util import get_remote_address

# Global flag
DISABLE_RATE_LIMIT = os.getenv("OMNIAI_DISABLE_RATE_LIMIT", "0").lower() in ("1", "true", "yes")

# Real limiter (only used if enabled)
_real_limiter = Limiter(key_func=get_remote_address)

def conditional_limit(limit: str) -> Callable[..., Callable[..., Coroutine[Any, Any, Any]]]:
    """Apply rate limit only if OMNIAI_DISABLE_RATE_LIMIT is not set."""
    if DISABLE_RATE_LIMIT:
        def decorator(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Coroutine[Any, Any, Any]]:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    else:
        return _real_limiter.limit(limit)