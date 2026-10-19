# backend/tests/integration/test_exception_handlers.py
"""
Integration tests for main.py's global exception handlers — verifies
every error path produces the {"detail": ..., "errors": ...} shape
that frontend/src/api/axiosClient.js's response interceptor depends
on to build its normalized error object.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.exceptions.custom_exceptions import AppException
from app.main import create_app


class SampleValidationModel(BaseModel):
    title: str


@pytest.fixture
def client_with_test_routes():
    """
    Mounts a couple of throwaway routes on a fresh app instance purely
    to trigger each exception handler path in isolation, without
    depending on any real endpoint module's business logic.
    """
    with patch("app.main.connect_to_mongo", new_callable=AsyncMock), \
         patch("app.main.ensure_indexes", new_callable=AsyncMock), \
         patch("app.main.start_scheduler"), \
         patch("app.main.shutdown_scheduler"), \
         patch("app.main.close_mongo_connection", new_callable=AsyncMock), \
         patch("app.main.ping_mongo", new_callable=AsyncMock, return_value=True):
        app = create_app()

        test_router = APIRouter()

        @test_router.get("/test-app-exception")
        async def raise_app_exception():
            raise AppException(status_code=404, detail="Thing not found.", errors=None)

        @test_router.get("/test-unhandled-exception")
        async def raise_unhandled():
            raise RuntimeError("Something exploded unexpectedly.")

        @test_router.post("/test-validation-route")
        async def post_validation(payload: SampleValidationModel):
            return payload.model_dump()

        app.include_router(test_router, prefix="/api/v1/_test")

        with TestClient(app, raise_server_exceptions=False) as c:
            yield c


class TestAppExceptionHandler:
    def test_returns_the_exceptions_declared_status_code(self, client_with_test_routes):
        response = client_with_test_routes.get("/api/v1/_test/test-app-exception")
        assert response.status_code == 404

    def test_response_body_has_detail_field(self, client_with_test_routes):
        response = client_with_test_routes.get("/api/v1/_test/test-app-exception")
        assert "detail" in response.json()
        assert response.json()["detail"] == "Thing not found."

    def test_response_body_has_errors_field_even_when_none(self, client_with_test_routes):
        response = client_with_test_routes.get("/api/v1/_test/test-app-exception")
        assert "errors" in response.json()
        assert response.json()["errors"] is None


class TestValidationExceptionHandler:
    def test_missing_required_field_returns_422(self, client_with_test_routes):
        response = client_with_test_routes.post("/api/v1/_test/test-validation-route", json={})
        assert response.status_code == 422

    def test_validation_error_response_has_detail_and_errors_fields(self, client_with_test_routes):
        response = client_with_test_routes.post("/api/v1/_test/test-validation-route", json={})
        body = response.json()
        assert "detail" in body
        assert "errors" in body

    def test_validation_errors_map_field_path_to_message(self, client_with_test_routes):
        response = client_with_test_routes.post("/api/v1/_test/test-validation-route", json={})
        body = response.json()
        errors = body.get("errors")
        if isinstance(errors, dict):
            assert any("title" in k for k in errors.keys())
        elif isinstance(errors, list):
            assert any("title" in str(err) for err in errors)
        else:
            assert "title" in str(body)


class TestUnhandledExceptionHandler:
    def test_unhandled_exception_returns_500_not_a_raw_traceback(self, client_with_test_routes):
        response = client_with_test_routes.get("/api/v1/_test/test-unhandled-exception")
        assert response.status_code == 500
        assert response.headers["content-type"].startswith("application/json")

    def test_unhandled_exception_response_never_leaks_internal_error_text(self, client_with_test_routes):
        response = client_with_test_routes.get("/api/v1/_test/test-unhandled-exception")
        body = response.text
        assert "RuntimeError" not in body
        assert "Something exploded" not in body