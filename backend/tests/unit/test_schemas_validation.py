# backend/tests/unit/test_schemas_validation.py
"""
Tests for request-schema field validation across the domains most
likely to receive malformed input from the frontend forms we built
(TaskFormDialog, MeetingFormDialog, RuleBuilder).
"""

import pytest
from pydantic import ValidationError

from app.schemas.task_schema import TaskCreateRequest, TaskStatusUpdateRequest
from app.schemas.meeting_schema import MeetingCreateRequest
from app.schemas.automation_schema import RuleCreateRequest, RuleConditionSchema, RuleActionSchema
from app.schemas.email_schema import BulkActionRequest, SemanticSearchRequest


class TestTaskCreateRequest:
    def test_accepts_minimal_valid_payload_with_only_title(self):
        req = TaskCreateRequest(title="Send report")
        assert req.title == "Send report"
        assert req.due_date is None

    def test_rejects_payload_missing_required_title(self):
        with pytest.raises(ValidationError):
            TaskCreateRequest()

    def test_accepts_camel_case_due_date_from_frontend_payload(self):
        req = TaskCreateRequest.model_validate({"title": "Task", "dueDate": "2026-01-15"})
        assert str(req.due_date) == "2026-01-15"


class TestBulkActionRequest:
    def test_accepts_camel_case_email_ids_from_frontend(self):
        req = BulkActionRequest.model_validate({"emailIds": ["a", "b", "c"], "action": "archive"})
        assert req.email_ids == ["a", "b", "c"]

    def test_rejects_empty_action_field_missing(self):
        with pytest.raises(ValidationError):
            BulkActionRequest.model_validate({"emailIds": ["a"]})


class TestMeetingCreateRequest:
    def test_accepts_valid_iso_datetime_strings(self):
        req = MeetingCreateRequest(
            title="Standup",
            start_time="2026-01-15T09:00:00Z",
            end_time="2026-01-15T09:30:00Z",
        )
        assert req.end_time > req.start_time

    def test_rejects_malformed_datetime_string(self):
        with pytest.raises(ValidationError):
            MeetingCreateRequest(title="Standup", start_time="not-a-date", end_time="2026-01-15T09:30:00Z")

    def test_attendees_defaults_to_empty_list_when_omitted(self):
        req = MeetingCreateRequest(
            title="Standup", start_time="2026-01-15T09:00:00Z", end_time="2026-01-15T09:30:00Z"
        )
        assert req.attendees == []


class TestRuleCreateRequest:
    def test_accepts_a_full_valid_rule_payload(self):
        req = RuleCreateRequest(
            name="Auto-archive newsletters",
            conditions=[RuleConditionSchema(field="category", operator="equals", value="newsletters")],
            actions=[RuleActionSchema(type="archive")],
        )
        assert req.condition_logic == "AND"  # default
        assert len(req.conditions) == 1

    def test_rejects_rule_missing_name(self):
        with pytest.raises(ValidationError):
            RuleCreateRequest(
                conditions=[RuleConditionSchema(field="category", operator="equals", value="x")],
                actions=[RuleActionSchema(type="archive")],
            )

    def test_action_value_is_optional_for_valueless_actions_like_archive(self):
        action = RuleActionSchema(type="archive")
        assert action.value is None

    def test_action_value_can_be_set_for_actions_like_label(self):
        action = RuleActionSchema(type="label", value="Important")
        assert action.value == "Important"


class TestSemanticSearchRequest:
    def test_default_limit_is_ten(self):
        req = SemanticSearchRequest(query="budget approvals")
        assert req.limit == 10

    def test_accepts_custom_limit(self):
        req = SemanticSearchRequest(query="budget approvals", limit=3)
        assert req.limit == 3


class TestTaskStatusUpdateRequest:
    @pytest.mark.parametrize("status", ["pending", "in_progress", "completed", "dismissed"])
    def test_accepts_each_documented_status_value(self, status):
        # NOTE: the schema currently types `status` as a bare `str`
        # (see schemas/task_schema.py) rather than a Literal/Enum, so
        # this test documents expected values but doesn't yet enforce
        # them at the schema layer. Consider tightening
        # TaskStatusUpdateRequest.status to
        # Literal["pending","in_progress","completed","dismissed"]
        # so invalid values are rejected by FastAPI's 422 handler
        # instead of reaching the service layer.
        req = TaskStatusUpdateRequest(status=status)
        assert req.status == status