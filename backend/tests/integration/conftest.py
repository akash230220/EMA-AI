# backend/tests/integration/conftest.py
"""
Shared fixtures for integration tests.
"""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.auth.jwt_handler import get_current_user
from app.main import create_app

FAKE_USER_ID = "507f1f77bcf86cd799439011"


def _fake_current_user():
    return SimpleNamespace(
        id=FAKE_USER_ID,
        name="Test User",
        email="test.user@example.com",
        avatar_url=None,
        timezone="UTC",
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def app():
    """Returns a FastAPI app instance configured for testing."""
    return create_app()


@pytest.fixture
def authenticated_client(app):
    app.dependency_overrides[get_current_user] = _fake_current_user
    with patch("app.main.connect_to_mongo", new_callable=AsyncMock), \
         patch("app.main.ensure_indexes", new_callable=AsyncMock), \
         patch("app.main.start_scheduler"), \
         patch("app.main.shutdown_scheduler"), \
         patch("app.main.close_mongo_connection", new_callable=AsyncMock), \
         patch("app.main.ping_mongo", new_callable=AsyncMock, return_value=True):
        with TestClient(app) as client:
            yield client
    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client(app):
    with patch("app.main.connect_to_mongo", new_callable=AsyncMock), \
         patch("app.main.ensure_indexes", new_callable=AsyncMock), \
         patch("app.main.start_scheduler"), \
         patch("app.main.shutdown_scheduler"), \
         patch("app.main.close_mongo_connection", new_callable=AsyncMock), \
         patch("app.main.ping_mongo", new_callable=AsyncMock, return_value=True):
        with TestClient(app) as client:
            yield client


@pytest.fixture
def fake_user_id():
    return FAKE_USER_ID

