
import time
from typing import Any, Awaitable, Callable
from starlette.requests import Request
from omniai.core.metrics_config import REQUEST_COUNT, REQUEST_LATENCY

class MetricsMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[dict[str, Any]]],
        send: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        start_time = time.time()
        status_code = 500  # default for errors

        async def send_wrapper(message: dict[str, Any]) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            raise
        finally:
            duration = time.time() - start_time
            endpoint = request.url.path
            REQUEST_LATENCY.labels(request.method, endpoint).observe(duration)
            REQUEST_COUNT.labels(request.method, endpoint, str(status_code)).inc()