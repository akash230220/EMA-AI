# backend/app/middlewares/rate_limiter.py
"""
In-Memory Sliding Window Rate Limiting Middleware.

Responsibilities:
  - Tracks request counts per client IP within a sliding 60-second window
  - Injects rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)
  - Returns HTTP 429 Too Many Requests when limits are exceeded
  - Skips non-rate-limited operational endpoints (/api/health, docs, openapi)
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Callable, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings

logger = logging.getLogger("ai_email_os.rate_limiter")
settings = get_settings()

EXEMPT_PATHS = {
    "/",
    "/api/health",
    "/api/docs",
    "/api/redoc",
    "/api/openapi.json",
    "/openapi.json",
    "/favicon.ico",
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window in-memory rate limiter per client IP.
    """

    def __init__(
        self,
        app,
        requests_per_minute: Optional[int] = None,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute or settings.RATE_LIMIT_PER_MINUTE
        # Map: client_ip -> list of timestamps
        self.request_history: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        """Extracts client IP from X-Forwarded-For header or direct client host."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "127.0.0.1"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Bypass rate limiting for operational & health routes
        if path in EXEMPT_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        now = time.time()
        window_start = now - 60.0

        # Clean timestamps older than 60 seconds
        timestamps = [t for t in self.request_history[client_ip] if t > window_start]
        self.request_history[client_ip] = timestamps

        if len(timestamps) >= self.requests_per_minute:
            oldest_timestamp = timestamps[0]
            retry_after = int(max(1, 60.0 - (now - oldest_timestamp)))

            logger.warning(
                "Rate limit exceeded for IP %s on %s %s (requests: %d/%d)",
                client_ip,
                request.method,
                path,
                len(timestamps),
                self.requests_per_minute,
            )

            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Rate limit exceeded. Please try again later.",
                    "errors": {"retry_after_seconds": retry_after},
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + retry_after)),
                },
            )

        # Record this request
        self.request_history[client_ip].append(now)
        remaining = max(0, self.requests_per_minute - len(self.request_history[client_ip]))

        response = await call_next(request)

        # Inject rate limit headers on response
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(now + 60.0))

        return response

