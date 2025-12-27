# omniai/core/middleware/logging_middleware.py
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from structlog.contextvars import bind_contextvars, clear_contextvars
from omniai.core.logging import logger

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Clear any leftover context from previous requests (important in async!)
        clear_contextvars()

        # Generate a unique trace ID for this request
        trace_id = str(uuid.uuid4())
        bind_contextvars(trace_id=trace_id)

        # Log request start
        logger.info(
            "http_request_start",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else "unknown"
        )

        try:
            response: Response = await call_next(request)
            # Log request end
            logger.info(
                "http_request_end",
                status_code=response.status_code,
                content_length=getattr(response, "content_length", 0)
            )
            return response
        except Exception as e:
            # Log unhandled exceptions
            logger.exception("http_request_unhandled_error", error=str(e))
            raise