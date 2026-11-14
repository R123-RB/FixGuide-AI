"""FastAPI middleware."""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("fixguide.api")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Request/response logging middleware."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Log request timing and outcome for each HTTP call."""
        start_time = time.time()

        # Log request
        logger.info(
            "request_started",
            extra={
                "method": request.method,
                "url": str(request.url),
                "client": request.client.host if request.client else None,
            },
        )

        response = await call_next(request)

        # Log response
        duration = time.time() - start_time
        logger.info(
            "request_completed",
            extra={
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            },
        )

        return response
