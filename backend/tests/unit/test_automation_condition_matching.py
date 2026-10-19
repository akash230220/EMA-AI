# backend/tests/unit/test_automation_condition_matching.py
"""
Tests for the automation rule condition-matching logic. This is a
forward-looking test file: it defines and tests a pure, dependency-
free `matches_condition(email_fields, condition)` function that
services/automation_service.py's test_rule()/rule evaluation during
the pipeline should implement. Included here (with the reference
implementation inline) since this logic is easy to get subtly wrong
and benefits from being specified via tests before the real service
module is written.

Once app/services/automation_service.py exists with a real
`evaluate_conditions()` function, replace the inline implementation
below with `from app.services.automation_service import evaluate_conditions`
and delete the local copy.
"""

import pytest


def matches_condition(email_fields: dict, condition: dict) -> bool:
    """Reference implementation — mirrors what automation_service.py should provide."""
    field_value = str(email_fields.get(condition["field"], "")).lower()
    target_value = str(condition["value"]).lower()
    operator = condition["operator"]

    if operator == "equals":
        return field_value == target_value
    if operator == "not_equals":
        return field_value != target_value
    if operator == "contains":
        return target_value in field_value
    if operator == "starts_with":
        return field_value.startswith(target_value)
    raise ValueError(f"Unknown operator: {operator}")


def evaluate_conditions(email_fields: dict, conditions: list[dict], logic: str = "AND") -> bool:
    results = [matches_condition(email_fields, c) for c in conditions]
    if logic == "OR":
        return any(results)
    return all(results)


class TestMatchesConditionOperators:
    def test_equals_operator_matches_exact_value(self):
        assert matches_condition({"category": "newsletters"}, {"field": "category", "operator": "equals", "value": "newsletters"}) is True

    def test_equals_operator_is_case_insensitive(self):
        assert matches_condition({"category": "Newsletters"}, {"field": "category", "operator": "equals", "value": "newsletters"}) is True

    def test_equals_operator_does_not_match_different_value(self):
        assert matches_condition({"category": "work"}, {"field": "category", "operator": "equals", "value": "newsletters"}) is False

    def test_not_equals_operator_inverts_equals(self):
        assert matches_condition({"category": "work"}, {"field": "category", "operator": "not_equals", "value": "newsletters"}) is True

    def test_contains_operator_matches_substring(self):
        assert matches_condition({"subject": "Your Invoice #4521"}, {"field": "subject", "operator": "contains", "value": "invoice"}) is True

    def test_contains_operator_does_not_match_absent_substring(self):
        assert matches_condition({"subject": "Team standup notes"}, {"field": "subject", "operator": "contains", "value": "invoice"}) is False

    def test_starts_with_operator_matches_prefix(self):
        assert matches_condition({"sender_email": "noreply@newsletter.com"}, {"field": "sender_email", "operator": "starts_with", "value": "noreply"}) is True

    def test_missing_field_is_treated_as_empty_string_not_a_crash(self):
        assert matches_condition({}, {"field": "category", "operator": "equals", "value": "work"}) is False

    def test_unknown_operator_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown operator"):
            matches_condition({"category": "work"}, {"field": "category", "operator": "greater_than", "value": "5"})


class TestEvaluateConditionsLogic:
    def test_and_logic_requires_all_conditions_to_match(self):
        conditions = [
            {"field": "category", "operator": "equals", "value": "newsletters"},
            {"field": "priority", "operator": "equals", "value": "low"},
        ]
        email = {"category": "newsletters", "priority": "low"}
        assert evaluate_conditions(email, conditions, logic="AND") is True

    def test_and_logic_fails_if_any_single_condition_fails(self):
        conditions = [
            {"field": "category", "operator": "equals", "value": "newsletters"},
            {"field": "priority", "operator": "equals", "value": "high"},
        ]
        email = {"category": "newsletters", "priority": "low"}
        assert evaluate_conditions(email, conditions, logic="AND") is False

    def test_or_logic_passes_if_any_single_condition_matches(self):
        conditions = [
            {"field": "category", "operator": "equals", "value": "newsletters"},
            {"field": "priority", "operator": "equals", "value": "high"},
        ]
        email = {"category": "work", "priority": "high"}
        assert evaluate_conditions(email, conditions, logic="OR") is True

    def test_or_logic_fails_only_if_no_conditions_match(self):
        conditions = [
            {"field": "category", "operator": "equals", "value": "newsletters"},
            {"field": "priority", "operator": "equals", "value": "high"},
        ]
        email = {"category": "work", "priority": "low"}
        assert evaluate_conditions(email, conditions, logic="OR") is False

    def test_empty_conditions_list_with_and_logic_returns_true(self):
        # A rule with no conditions matches everything under AND
        # (vacuous truth) — worth an explicit test since this is a
        # common off-by-one bug source.
        assert evaluate_conditions({"category": "work"}, [], logic="AND") is True

    def test_empty_conditions_list_with_or_logic_returns_false(self):
        assert evaluate_conditions({"category": "work"}, [], logic="OR") is False