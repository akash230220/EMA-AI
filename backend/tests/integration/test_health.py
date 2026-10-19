# backend/tests/integration/test_health.py
"""
Integration tests for the health-check and root endpoints defined
directly in main.py (not under api/v1/ — no auth, no versioning).
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    with patch("app.main.connect_to_mongo", new_callable=AsyncMock), \
         patch("app.main.ensure_indexes", new_callable=AsyncMock), \
         patch("app.main.start_scheduler"), \
         patch("app.main.shutdown_scheduler"), \
         patch("app.main.close_mongo_connection", new_callable=AsyncMock), \
         patch("app.main.ping_mongo", new_callable=AsyncMock, return_value=True):
        app = create_app()
        with TestClient(app) as c:
            yield c


class TestRootEndpoint:
    def test_root_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_service_metadata(self, client):
        response = client.get("/")
        body = response.json()
        assert body["service"] == "AI Email OS API"
        assert body["status"] == "running"
        assert body["docs"] == "/api/docs"


class TestHealthEndpoint:
    def test_health_returns_200_when_mongo_is_up(self, client):
        with patch("app.main.ping_mongo", new_callable=AsyncMock, return_value=True):
            response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["mongo_connected"] is True

    def test_health_reports_degraded_when_mongo_is_down(self, client):
        with patch("app.main.ping_mongo", new_callable=AsyncMock, return_value=False):
            response = client.get("/api/health")
        assert response.status_code == 200  # still 200 — "degraded" is a body field, not an HTTP error
        assert response.json()["status"] == "degraded"
        assert response.json()["mongo_connected"] is False

    def test_health_includes_current_environment(self, client):
        with patch("app.main.ping_mongo", new_callable=AsyncMock, return_value=True):
            response = client.get("/api/health")
        assert "environment" in response.json()