# backend/app/middlewares/cors_middleware.py
"""
CORS Middleware Configuration Helper.

Configures FastAPI Cross-Origin Resource Sharing with allowed origins,
methods, headers, credentials, and exposed headers for file downloads.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

settings = get_settings()


def setup_cors(app: FastAPI) -> None:
    """Configures CORS middleware on the provided FastAPI application instance."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
        expose_headers=["Content-Disposition", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )

