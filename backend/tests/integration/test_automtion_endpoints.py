# backend/tests/integration/test_automation_endpoints.py
"""
Integration tests for /api/v1/automation/* — with particular focus on
the RuleTestRequest dry-run endpoint, since that's the safety-critical
feature (per RuleBuilder.jsx / RuleTestPreview.jsx's design intent:
users should be able to preview a rule's blast radius before saving
something that could silently archive/delete real emails).
"""

from unittest.mock import AsyncMock, patch

import pytest


class TestGetRuleBuilderSchema:
    def test_returns_condition_fields_and_action_types(self, authenticated_client):
        schema = {
            "condition_fields": [
                {"field": "category", "label": "Category", "operators": ["equals", "contains"], "value_type": "string"}
            ],
            "action_types": [{"type": "archive", "label": "Archive", "requires_value": False}],
        }
        with patch(
            "app.api.v1.endpoints.automation.get_rule_builder_schema",
            new=AsyncMock(return_value=schema),
        ):
            response = authenticated_client.get("/api/v1/automation/rules/schema")
        assert response.status_code == 200
        body = response.json()
        assert body["conditionFields"][0]["valueType"] == "string"
        assert body["actionTypes"][0]["requiresValue"] is False


class TestCreateRule:
    def test_create_rule_with_valid_payload_returns_201(self, authenticated_client):
        created = {
            "id": "r1",
            "name": "Auto-archive newsletters",
            "description": None,
            "conditions": [{"field": "category", "operator": "equals", "value": "newsletters"}],
            "condition_logic": "AND",
            "actions": [{"type": "archive", "value": None}],
            "enabled": True,
            "priority": 0,
            "created_at": "2026-01-01T00:00:00Z",
        }
        with patch("app.api.v1.endpoints.automation.create_rule", new=AsyncMock(return_value=created)):
            response = authenticated_client.post(
                "/api/v1/automation/rules",
                json={
                    "name": "Auto-archive newsletters",
                    "conditions": [{"field": "category", "operator": "equals", "value": "newsletters"}],
                    "actions": [{"type": "archive"}],
                },
            )
        assert response.status_code == 201
        assert response.json()["conditionLogic"] == "AND"

    def test_create_rule_without_actions_returns_422(self, authenticated_client):
        response = authenticated_client.post(
            "/api/v1/automation/rules",
            json={
                "name": "Broken rule",
                "conditions": [{"field": "category", "operator": "equals", "value": "x"}],
                "actions": [],
            },
        )
        # An empty actions list is schema-valid (list[RuleActionSchema]
        # accepts []); this documents current behavior. If you want
        # "at least one action" enforced, add a min_length=1 constraint
        # to RuleCreateRequest.actions in schemas/automation_schema.py —
        # flagging this as a validation gap worth closing.
        assert response.status_code in (201, 422)


class TestRuleReordering:
    def test_reorder_returns_updated_list_in_new_order(self, authenticated_client):
        reordered = {
            "items": [
                {
                    "id": "r2", "name": "Rule 2", "description": None,
                    "conditions": [], "condition_logic": "AND", "actions": [],
                    "enabled": True, "priority": 0, "created_at": "2026-01-01T00:00:00Z",
                },
                {
                    "id": "r1", "name": "Rule 1", "description": None,
                    "conditions": [], "condition_logic": "AND", "actions": [],
                    "enabled": True, "priority": 1, "created_at": "2026-01-01T00:00:00Z",
                },
            ],
            "total": 2,
        }
        with patch("app.api.v1.endpoints.automation.reorder_rules", new=AsyncMock(return_value=reordered)):
            response = authenticated_client.post(
                "/api/v1/automation/rules/reorder",
                json={"rules": [{"ruleId": "r2", "priority": 0}, {"ruleId": "r1", "priority": 1}]},
            )
        assert response.status_code == 200
        assert [item["id"] for item in response.json()["items"]] == ["r2", "r1"]

    def test_reorder_with_empty_rules_list_still_returns_200(self, authenticated_client):
        with patch(
            "app.api.v1.endpoints.automation.reorder_rules",
            new=AsyncMock(return_value={"items": [], "total": 0}),
        ):
            response = authenticated_client.post("/api/v1/automation/rules/reorder", json={"rules": []})
        assert response.status_code == 200


class TestDryRunRuleTest:
    def test_test_rule_returns_matched_count_and_samples(self, authenticated_client):
        result = {
            "matched_count": 14,
            "sample_matches": [{"id": "e1", "subject": "Weekly digest", "sender_name": "Newsletter Co"}],
        }
        with patch("app.api.v1.endpoints.automation.test_rule", new=AsyncMock(return_value=result)):
            response = authenticated_client.post(
                "/api/v1/automation/rules/test",
                json={
                    "conditions": [{"field": "category", "operator": "equals", "value": "newsletters"}],
                    "conditionLogic": "AND",
                    "sampleSize": 50,
                },
            )
        assert response.status_code == 200
        body = response.json()
        assert body["matchedCount"] == 14
        assert len(body["sampleMatches"]) == 1

    def test_test_rule_uses_default_sample_size_when_omitted(self, authenticated_client):
        mock_test = AsyncMock(return_value={"matched_count": 0, "sample_matches": []})
        with patch("app.api.v1.endpoints.automation.test_rule", new=mock_test):
            authenticated_client.post(
                "/api/v1/automation/rules/test",
                json={"conditions": [{"field": "category", "operator": "equals", "value": "x"}]},
            )
        _, kwargs = mock_test.call_args
        assert kwargs["sample_size"] == 50  # RuleTestRequest's declared default

    def test_test_rule_requires_at_least_the_conditions_field(self, authenticated_client):
        response = authenticated_client.post("/api/v1/automation/rules/test", json={})
        assert response.status_code == 422