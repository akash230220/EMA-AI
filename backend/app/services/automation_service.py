# backend/app/services/automation_service.py
"""
Automation rules service.

Responsibilities:
  - list_rules          — paginated rule list (AutomationRulesPage)
  - get_rule_by_id      — single rule detail
  - create_rule         — new automation rule
  - update_rule         — rule field update
  - set_rule_enabled    — toggle enabled/disabled
  - reorder_rules       — update priority ordering
  - delete_rule         — remove rule
  - test_rule           — dry-run against recent emails (RuleTestPreview)
  - get_rule_execution_logs — audit log per rule (RuleExecutionLogDialog)
  - get_rule_builder_schema — available fields/operators/actions for the
                              RuleBuilder UI (keeps frontend in sync)

Actual rule evaluation during inbox sync is done by
ai/agents/automation_agent.py (called from the LangGraph pipeline).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from app.exceptions.custom_exceptions import AppException
from app.models.automation_rule import AutomationRuleModel, RuleAction, RuleCondition
from app.repositories.automation_repository import (
    AutomationRuleRepository,
    RuleExecutionLogRepository,
)
from app.repositories.email_repository import EmailRepository
from app.schemas.automation_schema import (
    RuleBuilderSchemaResponse,
    RuleConditionSchema,
    RuleActionSchema,
    RuleCreateRequest,
    RuleExecutionLogListResponse,
    RuleExecutionLogResponse,
    RuleListResponse,
    RuleResponse,
    RuleReorderItem,
    RuleTestResponse,
    RuleTestMatchResponse,
    RuleUpdateRequest,
)

logger = logging.getLogger("ai_email_os.automation_service")


# ---------------------------------------------------------------------------
# Mapping helper
# ---------------------------------------------------------------------------

def _to_response(rule: AutomationRuleModel) -> RuleResponse:
    return RuleResponse(
        id=str(rule.id),
        name=rule.name,
        description=rule.description,
        conditions=[
            RuleConditionSchema(field=c.field, operator=c.operator, value=c.value)
            for c in rule.conditions
        ],
        condition_logic=rule.condition_logic,
        actions=[
            RuleActionSchema(type=a.type, value=a.value)
            for a in rule.actions
        ],
        enabled=rule.enabled,
        priority=rule.priority,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


# ---------------------------------------------------------------------------
# Rule condition evaluator (for test_rule dry-run)
# ---------------------------------------------------------------------------

def _evaluate_condition(email_doc: dict[str, Any], condition: RuleCondition) -> bool:
    """Evaluates a single condition against an email document."""
    field_map = {
        "category": "category",
        "priority": "priority",
        "intent": "intent",
        "sentiment": "sentiment",
        "sender_domain": "sender_email",
        "sender_email": "sender_email",
        "subject": "subject",
    }
    doc_field = field_map.get(condition.field, condition.field)
    raw_value: str = str(email_doc.get(doc_field, "") or "")

    # Extract domain for sender_domain field
    if condition.field == "sender_domain" and "@" in raw_value:
        raw_value = raw_value.split("@", 1)[1]

    rule_value = condition.value.lower()
    raw_lower = raw_value.lower()

    if condition.operator == "equals":
        return raw_lower == rule_value
    elif condition.operator == "not_equals":
        return raw_lower != rule_value
    elif condition.operator == "contains":
        return rule_value in raw_lower
    elif condition.operator == "starts_with":
        return raw_lower.startswith(rule_value)
    elif condition.operator == "ends_with":
        return raw_lower.endswith(rule_value)
    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def list_rules(
    user_id: str,
    enabled_only: Optional[bool] = None,
    sort_by: str = "priority",
    sort_order: str = "asc",
) -> RuleListResponse:
    repo = AutomationRuleRepository()
    rules, total = await repo.list_for_user(
        user_id=user_id,
        enabled=True if enabled_only else None,
    )
    return RuleListResponse(
        items=[_to_response(r) for r in rules],
        total=total,
    )


async def get_rule_by_id(user_id: str, rule_id: str) -> RuleResponse:
    repo = AutomationRuleRepository()
    rule = await repo.find_one({"_id": rule_id, "user_id": user_id})
    if not rule:
        raise AppException(status_code=404, detail="Automation rule not found.")
    return _to_response(rule)


async def create_rule(user_id: str, payload: RuleCreateRequest) -> RuleResponse:
    from app.repositories.user_repository import UserRepository  # noqa: PLC0415
    user = await UserRepository().get_by_id(user_id)
    if not user:
        raise AppException(status_code=404, detail="User not found.")

    now = datetime.now(timezone.utc)
    rule = AutomationRuleModel(
        user_id=user.id,
        name=payload.name,
        description=payload.description,
        conditions=[
            RuleCondition(field=c.field, operator=c.operator, value=c.value)
            for c in payload.conditions
        ],
        condition_logic=payload.condition_logic,
        actions=[
            RuleAction(type=a.type, value=a.value)
            for a in payload.actions
        ],
        enabled=payload.enabled if payload.enabled is not None else True,
        priority=payload.priority if payload.priority is not None else 0,
        created_at=now,
        updated_at=now,
    )
    repo = AutomationRuleRepository()
    saved = await repo.insert_one(rule)
    logger.info("Automation rule created: id=%s user_id=%s", saved.id, user_id)
    return _to_response(saved)


async def update_rule(
    user_id: str, rule_id: str, payload: RuleUpdateRequest
) -> RuleResponse:
    repo = AutomationRuleRepository()
    rule = await repo.find_one({"_id": rule_id, "user_id": user_id})
    if not rule:
        raise AppException(status_code=404, detail="Automation rule not found.")

    updates: dict = {"updated_at": datetime.now(timezone.utc)}
    if payload.name is not None:
        updates["name"] = payload.name
    if payload.description is not None:
        updates["description"] = payload.description
    if payload.conditions is not None:
        updates["conditions"] = [c.model_dump() for c in payload.conditions]
    if payload.condition_logic is not None:
        updates["condition_logic"] = payload.condition_logic
    if payload.actions is not None:
        updates["actions"] = [a.model_dump() for a in payload.actions]
    if payload.priority is not None:
        updates["priority"] = payload.priority

    updated = await repo.update_one(
        {"_id": rule.id, "user_id": user_id},
        {"$set": updates},
    )
    if not updated:
        raise AppException(status_code=404, detail="Automation rule not found.")
    return _to_response(updated)


async def set_rule_enabled(user_id: str, rule_id: str, enabled: bool) -> RuleResponse:
    repo = AutomationRuleRepository()
    updated = await repo.toggle(rule_id=rule_id, user_id=user_id, enabled=enabled)
    if not updated:
        raise AppException(status_code=404, detail="Automation rule not found.")
    return _to_response(updated)


async def reorder_rules(user_id: str, rules: list[RuleReorderItem]) -> RuleListResponse:
    """
    Applies a new priority ordering to a list of rules.
    The frontend RuleList sends the full ordered list after drag-and-drop.
    """
    repo = AutomationRuleRepository()
    for i, item in enumerate(rules):
        await repo.update_one(
            {"_id": item.id, "user_id": user_id},
            {"$set": {"priority": i, "updated_at": datetime.now(timezone.utc)}},
        )
    # Return the updated list in priority order
    updated_rules, total = await repo.list_for_user(user_id=user_id)
    return RuleListResponse(items=[_to_response(r) for r in updated_rules], total=total)


async def delete_rule(user_id: str, rule_id: str) -> None:
    repo = AutomationRuleRepository()
    deleted = await repo.delete_one({"user_id": user_id, "_id": rule_id})
    if not deleted:
        raise AppException(status_code=404, detail="Automation rule not found.")


async def test_rule(
    user_id: str,
    conditions: list[RuleConditionSchema],
    condition_logic: str = "AND",
    sample_size: int = 20,
) -> RuleTestResponse:
    """
    Dry-runs a set of conditions against the user's recent emails.
    Does NOT apply any actions — purely evaluates matches.
    Used by RuleTestPreview.jsx before the rule is saved.
    """
    email_repo = EmailRepository()
    emails, _ = await email_repo.list_for_user(
        user_id=user_id,
        page=1,
        page_size=sample_size,
        sort_by="received_at",
        sort_order="desc",
    )

    rule_conditions = [
        RuleCondition(field=c.field, operator=c.operator, value=c.value)
        for c in conditions
    ]

    matches: list[RuleTestMatchResponse] = []
    for email in emails:
        email_doc = {
            "category": email.category,
            "priority": email.priority,
            "intent": email.intent,
            "sentiment": email.sentiment,
            "sender_email": email.sender_email,
            "subject": email.subject,
        }
        condition_results = [_evaluate_condition(email_doc, c) for c in rule_conditions]

        if condition_logic.upper() == "AND":
            matched = all(condition_results)
        else:
            matched = any(condition_results)

        if matched:
            matches.append(
                RuleTestMatchResponse(
                    email_id=str(email.id),
                    subject=email.subject,
                    sender_email=email.sender_email,
                    category=email.category,
                    priority=email.priority,
                )
            )

    return RuleTestResponse(
        matched_count=len(matches),
        sample_size=len(emails),
        matches=matches,
    )


async def get_rule_execution_logs(
    user_id: str, rule_id: str, page: int = 1, page_size: int = 20
) -> RuleExecutionLogListResponse:
    """
    Returns the execution audit log for a specific automation rule.
    Powers RuleExecutionLogDialog.jsx.
    """
    log_repo = RuleExecutionLogRepository()
    logs, total = await log_repo.list_for_user_and_rule(
        user_id=user_id, rule_id=rule_id, page=page, page_size=page_size
    )
    return RuleExecutionLogListResponse(
        items=[
            RuleExecutionLogResponse(
                id=str(log.id),
                rule_id=str(log.rule_id),
                email_id=str(log.email_id),
                email_subject=log.email_subject,
                actions_performed=[
                    RuleActionSchema(type=a.type, value=a.value)
                    for a in log.actions_performed
                ],
                success=log.success,
                error_message=log.error_message,
                executed_at=log.executed_at,
            )
            for log in logs
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_rule_builder_schema() -> RuleBuilderSchemaResponse:
    """
    Returns the static schema of available condition fields, operators,
    and action types. Consumed by the RuleBuilder UI to render its
    dropdowns and keep them in sync with backend capabilities.
    """
    return RuleBuilderSchemaResponse(
        condition_fields=[
            {"field": "category", "label": "Category",
             "operators": ["equals", "not_equals"],
             "options": ["work", "finance", "personal", "newsletters", "promotions", "social"]},
            {"field": "priority", "label": "Priority",
             "operators": ["equals", "not_equals"],
             "options": ["high", "medium", "low"]},
            {"field": "intent", "label": "Intent",
             "operators": ["equals", "not_equals"],
             "options": ["meeting_request", "task", "fyi", "follow_up", "urgent_action", "question"]},
            {"field": "sentiment", "label": "Sentiment",
             "operators": ["equals", "not_equals"],
             "options": ["positive", "neutral", "negative"]},
            {"field": "sender_email", "label": "Sender Email",
             "operators": ["equals", "contains", "starts_with", "ends_with"],
             "options": []},
            {"field": "sender_domain", "label": "Sender Domain",
             "operators": ["equals", "contains"],
             "options": []},
            {"field": "subject", "label": "Subject",
             "operators": ["contains", "starts_with", "ends_with"],
             "options": []},
        ],
        action_types=[
            {"type": "archive", "label": "Archive email", "has_value": False},
            {"type": "delete", "label": "Delete email", "has_value": False},
            {"type": "mark_read", "label": "Mark as read", "has_value": False},
            {"type": "label", "label": "Apply label", "has_value": True, "value_label": "Label name"},
            {"type": "forward", "label": "Forward to", "has_value": True, "value_label": "Email address"},
            {"type": "auto_reply", "label": "Auto-reply with", "has_value": True, "value_label": "Reply text"},
            {"type": "notify", "label": "Send notification", "has_value": False},
        ],
        condition_logic_options=["AND", "OR"],
    )

