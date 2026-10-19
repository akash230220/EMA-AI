# backend/tests/integration/test_auth_dependency.py
"""
Integration tests verifying that protected routes actually enforce
authentication — i.e. Depends(get_current_user) is wired correctly
across every router, not bypassable by accident.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

PROTECTED_GET_ENDPOINTS = [
    "/api/v1/auth/me",
    "/api/v1/inbox/sync/status",
    "/api/v1/emails",
    "/api/v1/tasks",
    "/api/v1/tasks/stats",
    "/api/v1/meetings",
    "/api/v1/meetings/upcoming",
    "/api/v1/analytics/summary",
    "/api/v1/automation/rules",
    "/api/v1/automation/rules/schema",
    "/api/v1/copilot/conversations",
    "/api/v1/settings",
]


class TestProtectedEndpointsRejectAnonymousRequests:
    @pytest.mark.parametrize("path", PROTECTED_GET_ENDPOINTS)
    def test_returns_401_or_403_without_auth(self, unauthenticated_client, path):
        response = unauthenticated_client.get(path)
        assert response.status_code in (401, 403)


class TestProtectedEndpointsAcceptAuthenticatedRequests:
    @pytest.mark.parametrize("path", PROTECTED_GET_ENDPOINTS)
    def test_does_not_return_401_or_403_when_authenticated(self, authenticated_client, path):
        now = datetime.now(timezone.utc)
        with patch("app.repositories.base.BaseRepository.find_many", new_callable=AsyncMock, return_value=[]), \
             patch("app.repositories.base.BaseRepository.find_one", new_callable=AsyncMock, return_value=None), \
             patch("app.repositories.base.BaseRepository.count_documents", new_callable=AsyncMock, return_value=0), \
             patch("app.repositories.email_repository.EmailRepository.list_for_user", new_callable=AsyncMock, return_value=([], 0)), \
             patch("app.repositories.task_repository.TaskRepository.list_for_user", new_callable=AsyncMock, return_value=([], 0)), \
             patch("app.repositories.meeting_repository.MeetingRepository.list_for_user", new_callable=AsyncMock, return_value=([], 0)), \
             patch("app.repositories.automation_repository.AutomationRuleRepository.list_for_user", new_callable=AsyncMock, return_value=([], 0)), \
             patch("app.api.v1.endpoints.inbox.get_sync_status", new_callable=AsyncMock, return_value={"status": "idle", "last_synced_at": None}), \
             patch("app.api.v1.endpoints.analytics.get_dashboard_summary", new_callable=AsyncMock, return_value={
                 "total_emails": 0, "high_priority_emails": 0, "pending_replies": 0, "meetings": 0, "tasks": 0, "ai_replies_generated": 0, "ai_time_saved_minutes": 0,
             }), \
             patch("app.api.v1.endpoints.settings.get_user_settings", new_callable=AsyncMock, return_value={
                 "profile": {
                     "id": "507f1f77bcf86cd799439011",
                     "email": "test@example.com",
                     "name": "Test User",
                     "timezone": "UTC",
                     "avatar_url": None,
                     "created_at": now,
                 },
                 "gmail_status": {
                     "connected": True,
                     "email": "test@example.com",
                     "last_synced_at_label": None,
                 },
                 "calendar_status": {
                     "connected": True,
                     "email": "test@example.com",
                     "last_synced_at_label": None,
                 },
                 "notification_preferences": {
                     "high_priority_email": True,
                     "meeting_detected": True,
                     "task_detected": True,
                     "daily_brief": True,
                     "automation_fired": True,
                     "weekly_digest": True,
                 },
                 "ai_preferences": {
                     "default_reply_tone": "formal",
                     "summary_length": "standard",
                     "auto_process_new_emails": True,
                     "auto_sync_confirmed_meetings": True,
                 },
                 "sessions": [],
             }):
            response = authenticated_client.get(path)
            assert response.status_code not in (401, 403)