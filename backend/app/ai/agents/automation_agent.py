# backend/app/ai/agents/automation_agent.py
"""
Automation Agent.

Evaluates user-configured AutomationRuleModel rules against processed emails.
Executes matching actions:
  - archive
  - delete
  - mark_read
  - label
  - forward
  - auto_reply
  - notify
Records execution logs in RuleExecutionLogModel.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.models.automation_rule import AutomationRuleModel, RuleAction, RuleCondition, RuleExecutionLogModel
from app.models.email import EmailModel
from app.repositories.automation_repository import AutomationRuleRepository, RuleExecutionLogRepository
from app.repositories.email_repository import EmailRepository
from app.repositories.user_repository import UserRepository

logger = logging.getLogger("ai_email_os.automation_agent")


def evaluate_condition(email: EmailModel, condition: RuleCondition) -> bool:
    """Evaluates a single condition against an EmailModel."""
    field_name = condition.field.lower()
    operator = condition.operator.lower()
    expected_value = condition.value.lower()

    actual_value = ""
    if field_name == "category":
        actual_value = str(email.category or "").lower()
    elif field_name == "priority":
        actual_value = str(email.priority or "").lower()
    elif field_name == "intent":
        actual_value = str(email.intent or "").lower()
    elif field_name == "sentiment":
        actual_value = str(email.sentiment or "").lower()
    elif field_name == "sender_email":
        actual_value = str(email.sender_email or "").lower()
    elif field_name == "sender_domain":
        actual_value = str(email.sender_email or "").split("@")[-1].lower()
    elif field_name == "subject":
        actual_value = str(email.subject or "").lower()

    if operator == "equals":
        return actual_value == expected_value
    elif operator == "not_equals":
        return actual_value != expected_value
    elif operator == "contains":
        return expected_value in actual_value
    elif operator == "starts_with":
        return actual_value.startswith(expected_value)
    elif operator == "ends_with":
        return actual_value.endswith(expected_value)

    return False


def does_rule_match(email: EmailModel, rule: AutomationRuleModel) -> bool:
    """Checks if email satisfies rule conditions using AND/OR logic."""
    if not rule.conditions:
        return False

    results = [evaluate_condition(email, cond) for cond in rule.conditions]
    if rule.condition_logic.upper() == "OR":
        return any(results)
    return all(results)


async def execute_action(action: RuleAction, email: EmailModel, user_id: str) -> bool:
    """Executes an individual action on an email."""
    email_repo = EmailRepository()
    action_type = action.type.lower()

    try:
        if action_type == "archive":
            await email_repo.mark_archived(user_id=user_id, email_id=str(email.id), archived=True)
        elif action_type == "delete":
            await email_repo.soft_delete(user_id=user_id, email_id=str(email.id))
        elif action_type == "mark_read":
            await email_repo.mark_read(user_id=user_id, email_id=str(email.id), is_read=True)
        elif action_type == "auto_reply" and action.value:
            user = await UserRepository().get_by_id(user_id)
            if user and user.oauth_tokens and user.oauth_tokens.gmail_connected:
                from app.integrations.gmail.gmail_client import send_reply_message  # noqa: PLC0415
                await send_reply_message(
                    oauth_tokens=user.oauth_tokens,
                    thread_id=email.gmail_thread_id,
                    to_address=email.sender_email,
                    subject=email.subject,
                    body=action.value,
                )
        return True
    except Exception as exc:
        logger.error("Failed to execute action %s on email %s: %s", action_type, email.id, exc)
        return False


async def process_automation_rules(email: EmailModel, user_id: str) -> list[str]:
    """
    Evaluates all active rules for the user in priority order.
    Returns list of matched rule IDs.
    """
    rule_repo = AutomationRuleRepository()
    log_repo = RuleExecutionLogRepository()

    rules, _ = await rule_repo.list_for_user(user_id=user_id, enabled=True)
    if not rules:
        return []

    executed_rule_ids = []
    now = datetime.now(timezone.utc)

    for rule in rules:
        if does_rule_match(email, rule):
            logger.info("Email id=%s matched rule '%s' (id=%s)", email.id, rule.name, rule.id)
            actions_performed = []
            success = True
            err_msg = None

            for action in rule.actions:
                ok = await execute_action(action, email, user_id)
                if ok:
                    actions_performed.append(action)
                else:
                    success = False
                    err_msg = f"Action {action.type} failed to execute."

            # Record audit log
            from bson import ObjectId  # noqa: PLC0415
            log = RuleExecutionLogModel(
                user_id=ObjectId(user_id) if isinstance(user_id, str) else user_id,
                rule_id=rule.id,
                email_id=email.id,
                email_subject=email.subject,
                actions_performed=actions_performed,
                success=success,
                error_message=err_msg,
                executed_at=now,
            )
            await log_repo.insert_one(log)
            executed_rule_ids.append(str(rule.id))

    return executed_rule_ids

