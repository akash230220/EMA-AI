# backend/app/middlewares/error_handler.py
"""
Global Error Handling Middleware & Exception Formatters.

Responsibilities:
  - Catches unhandled exceptions during request processing
  - Returns consistent JSON response shapes ({ "detail": "...", "errors": ... })
  - Logs stack traces with request context (method, path, client IP)
  - Tracks request processing latency
"""

from __future__ import annotations

import logging
import time
from typing import Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.exceptions.custom_exceptions import AppException

logger = logging.getLogger("ai_email_os.error_handler")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs incoming requests and execution duration in milliseconds."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        method = request.method
        path = request.url.path

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000.0
            response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

            if path not in ("/api/health", "/"):
                logger.info(
                    "%s %s -> %d (%.2fms)",
                    method,
                    path,
                    response.status_code,
                    duration_ms,
                )
            return response
        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000.0
            logger.exception(
                "Unhandled exception processing %s %s after %.2fms: %s",
                method,
                path,
                duration_ms,
                exc,
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "An unexpected internal server error occurred.",
                    "errors": None,
                },
            )


def register_exception_handlers(app: FastAPI) -> None:
    """Registers standard exception handlers on the FastAPI app instance."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.warning(
            "AppException on %s %s [%d]: %s",
            request.method,
            request.url.path,
            exc.status_code,
            exc.detail,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "errors": exc.errors},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        field_errors = {}
        for err in exc.errors():
            loc = err.get("loc", [])
            field_path = ".".join(str(item) for item in loc if item != "body")
            field_errors[field_path or "_"] = err.get("msg", "Invalid value")

        logger.warning(
            "Validation error on %s %s: %s",
            request.method,
            request.url.path,
            field_errors,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Request payload validation failed.",
                "errors": field_errors,
            },
        )

