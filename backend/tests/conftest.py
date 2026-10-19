# backend/tests/conftest.py
"""
Shared pytest fixtures for both unit/ and integration/ test suites.
"""

import os

# Ensure tests never accidentally read a real .env / hit real
# external services — set safe dummy values before any app module
# (which calls get_settings() at import time) is imported.
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DB_NAME", "ai_email_os_test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production-use-only")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")

import pytest
from app.core.config import get_settings


@pytest.fixture(scope="session", autouse=True)
def _clear_settings_cache():
    """Ensures get_settings()'s lru_cache doesn't leak state between test runs invoked in the same process."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def settings():
    return get_settings()