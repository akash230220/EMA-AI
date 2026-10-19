# backend/app/models/automation_rule.py
"""Automation rule document + its execution log — trigger/condition/action pipeline configuration."""

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.models.base import MongoBaseModel, PyObjectId, utcnow


class RuleCondition(MongoBaseModel.__base__):
    model_config = {"populate_by_name": True}

    field: str  # e.g. "category", "sender_domain", "priority"
    operator: str  # equals | not_equals | contains | starts_with
    value: str


class RuleAction(MongoBaseModel.__base__):
    model_config = {"populate_by_name": True}

    type: str  # archive | delete | label | mark_read | forward | auto_reply | notify
    value: Optional[str] = None  # e.g. label name, forward-to email


class AutomationRuleModel(MongoBaseModel):
    """Collection: `automation_rules`"""

    user_id: PyObjectId
    name: str
    description: Optional[str] = None

    conditions: list[RuleCondition] = Field(default_factory=list)
    condition_logic: str = "AND"  # AND | OR
    actions: list[RuleAction] = Field(default_factory=list)

    enabled: bool = True
    priority: int = 0  # execution order — lower runs first

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class RuleExecutionLogModel(MongoBaseModel):
    """
    Collection: `rule_execution_logs` — audit trail of what an
    automation rule did, powering RuleExecutionLogDialog.jsx.
    """

    user_id: PyObjectId
    rule_id: PyObjectId
    email_id: PyObjectId
    email_subject: str  # denormalized for display without a join

    actions_performed: list[RuleAction] = Field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None

    executed_at: datetime = Field(default_factory=utcnow)