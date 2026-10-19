# backend/tests/integration/conftest.py
"""
Shared fixtures for integration tests. These tests exercise the real
FastAPI app (routing, middleware, exception handlers, the
get_current_user auth dependency) via httpx's TestClient, but stub
out app.auth.jwt_handler.get_current_user via FastAPI's own
dependency_overrides mechanism — this is the standard, supported way
to bypass real JWT verification in tests without touching app code.

Once services/ and repositories/ exist, individual test modules
additionally monkeypatch the specific service functions they exercise
(see test_tasks_endpoints.py for the pattern) rather than hitting a
real MongoDB — that keeps these tests fast and deterministic. A
separate tests/integration/test_full_stack.py (added once
db/mongo_client.py + mongomock-motor wiring exists) would be the
place for true DB-backed integration tests.
"""

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.auth.jwt_handler import get_current_user


FAKE_USER_ID = "507f1f77bcf86cd799439011"


def _fake_current_user():
    """
    Matches the shape auth/jwt_handler.get_current_user() is expected
    to return — a user-like object with at least `.id`, used by every
    endpoint handler as `current_user.id`. Kept as a SimpleNamespace
    rather than a real UserModel instance so this fixture has zero
    dependency on models/user.py's exact field list.
    """
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
    """Fresh FastAPI app instance per test — create_app() is a factory specifically to support this."""
    return create_app()


@pytest.fixture
def authenticated_client(app):
    """
    A TestClient where every route behind Depends(get_current_user)
    is automatically "authenticated" as FAKE_USER_ID, without needing
    a real JWT, Google OAuth flow, or database-backed user lookup.
    """
    app.dependency_overrides[get_current_user] = _fake_current_user
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client(app):
    """A TestClient with no auth override — used to verify protected routes actually reject anonymous requests."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def fake_user_id():
    return FAKE_USER_ID