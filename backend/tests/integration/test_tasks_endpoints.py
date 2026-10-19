# backend/tests/integration/test_tasks_endpoints.py
"""
Integration tests for /api/v1/tasks/* — request validation, response
shape, and status codes, with app.services.task_service functions
monkeypatched (since services/ doesn't exist as real code yet).

This file follows the pattern every other endpoint-domain integration
test file should adopt once services/ is generated: patch the
service-layer function the endpoint calls, assert on HTTP-level
behavior (status code, response shape, camelCase JSON keys) rather
than on database state.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest


def _sample_task_response(task_id="t1", **overrides):
    base = {
        "id": task_id,
        "title": "Send Q3 report",
        "description": None,
        "due_date": None,
        "due_date_label": None,
        "priority": "medium",
        "status": "pending",
        "source": "manual",
        "source_email_id": None,
        "created_at": datetime.now(timezone.utc),
    }
    base.update(overrides)
    return base


class TestCreateTask:
    def test_create_task_returns_201(self, authenticated_client):
        with patch(
            "app.api.v1.endpoints.tasks.create_task",
            new=AsyncMock(return_value=_sample_task_response()),
        ):
            response = authenticated_client.post("/api/v1/tasks", json={"title": "Send Q3 report"})
        assert response.status_code == 201

    def test_create_task_response_uses_camel_case_keys(self, authenticated_client):
        with patch(
            "app.api.v1.endpoints.tasks.create_task",
            new=AsyncMock(return_value=_sample_task_response()),
        ):
            response = authenticated_client.post("/api/v1/tasks", json={"title": "Send Q3 report"})
        body = response.json()
        assert "sourceEmailId" in body
        assert "dueDateLabel" in body
        assert "source_email_id" not in body

    def test_create_task_without_title_returns_422(self, authenticated_client):
        response = authenticated_client.post("/api/v1/tasks", json={})
        assert response.status_code == 422

    def test_create_task_accepts_camel_case_due_date_field(self, authenticated_client):
        mock_create = AsyncMock(return_value=_sample_task_response())
        with patch("app.api.v1.endpoints.tasks.create_task", new=mock_create):
            response = authenticated_client.post(
                "/api/v1/tasks", json={"title": "Task", "dueDate": "2026-02-01"}
            )
        assert response.status_code == 201
        # Verify the parsed request payload reached the service call
        # with the due_date field actually populated (proves the
        # camelCase alias -> snake_case Python attribute mapping works
        # end-to-end through the request schema, not just responses).
        _, kwargs = mock_create.call_args
        assert str(kwargs["payload"].due_date) == "2026-02-01"


class TestGetTasks:
    def test_get_tasks_returns_200_with_list_shape(self, authenticated_client):
        list_response = {
            "items": [_sample_task_response()],
            "total": 1,
            "page": 1,
            "page_size": 20,
        }
        with patch("app.api.v1.endpoints.tasks.list_tasks", new=AsyncMock(return_value=list_response)):
            response = authenticated_client.get("/api/v1/tasks")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["pageSize"] == 20
        assert len(body["items"]) == 1

    def test_get_tasks_forwards_camel_case_query_params_correctly(self, authenticated_client):
        mock_list = AsyncMock(return_value={"items": [], "total": 0, "page": 1, "page_size": 20})
        with patch("app.api.v1.endpoints.tasks.list_tasks", new=mock_list):
            authenticated_client.get("/api/v1/tasks?pageSize=50&sortBy=priority&sortOrder=desc")

        _, kwargs = mock_list.call_args
        assert kwargs["page_size"] == 50
        assert kwargs["sort_by"] == "priority"
        assert kwargs["sort_order"] == "desc"


class TestUpdateTaskStatus:
    def test_valid_status_transition_returns_200(self, authenticated_client):
        updated = _sample_task_response(status="completed")
        with patch(
            "app.api.v1.endpoints.tasks.update_task_status",
            new=AsyncMock(return_value=updated),
        ):
            response = authenticated_client.patch("/api/v1/tasks/t1/status", json={"status": "completed"})
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    def test_missing_status_field_returns_422(self, authenticated_client):
        response = authenticated_client.patch("/api/v1/tasks/t1/status", json={})
        assert response.status_code == 422


class TestBulkStatusUpdate:
    def test_bulk_update_returns_affected_count(self, authenticated_client):
        with patch(
            "app.api.v1.endpoints.tasks.bulk_update_task_status",
            new=AsyncMock(return_value=3),
        ):
            response = authenticated_client.post(
                "/api/v1/tasks/bulk/status",
                json={"taskIds": ["t1", "t2", "t3"], "status": "completed"},
            )
        assert response.status_code == 200
        assert response.json()["affected"] == 3

    def test_bulk_update_without_task_ids_returns_422(self, authenticated_client):
        response = authenticated_client.post("/api/v1/tasks/bulk/status", json={"status": "completed"})
        assert response.status_code == 422


class TestDeleteTask:
    def test_delete_task_returns_204(self, authenticated_client):
        with patch("app.api.v1.endpoints.tasks.delete_task", new=AsyncMock(return_value=None)):
            response = authenticated_client.delete("/api/v1/tasks/t1")
        assert response.status_code == 204
        assert response.content == b""