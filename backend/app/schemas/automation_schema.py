# backend/app/schemas/automation_schema.py
"""Automation rules and execution log schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import Field, model_validator

from app.schemas.common_schema import CamelModel


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------

class RuleConditionSchema(CamelModel):
    field: str
    operator: str
    value: str


class RuleActionSchema(CamelModel):
    type: str
    value: Optional[str] = None


class RuleReorderItem(CamelModel):
    id: str = Field(default="", alias="id")
    rule_id: Optional[str] = Field(default=None, alias="ruleId")

    @model_validator(mode="before")
    @classmethod
    def sync_ids(cls, data: Any) -> Any:
        if isinstance(data, dict):
            r_id = data.get("ruleId") or data.get("rule_id") or data.get("id", "")
            data["id"] = r_id
            data["ruleId"] = r_id
        return data


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class RuleCreateRequest(CamelModel):
    name: str
    description: Optional[str] = None
    conditions: list[RuleConditionSchema] = Field(default_factory=list)
    condition_logic: str = "AND"
    actions: list[RuleActionSchema] = Field(..., min_length=1)
    enabled: Optional[bool] = True
    priority: Optional[int] = 0


class RuleUpdateRequest(CamelModel):
    name: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[list[RuleConditionSchema]] = None
    condition_logic: Optional[str] = None
    actions: Optional[list[RuleActionSchema]] = None
    priority: Optional[int] = None


class RuleEnabledUpdateRequest(CamelModel):
    enabled: bool


class RuleReorderRequest(CamelModel):
    rules: list[RuleReorderItem] = Field(default_factory=list)


class RuleTestRequest(CamelModel):
    conditions: list[RuleConditionSchema]
    condition_logic: str = "AND"
    sample_size: int = 50


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class RuleResponse(CamelModel):
    id: str
    name: str
    description: Optional[str] = None
    conditions: list[RuleConditionSchema] = Field(default_factory=list)
    condition_logic: str
    actions: list[RuleActionSchema] = Field(default_factory=list)
    enabled: bool
    priority: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RuleListResponse(CamelModel):
    items: list[RuleResponse]
    total: int


class RuleTestMatchResponse(CamelModel):
    email_id: str = Field(default="", alias="emailId")
    subject: str
    sender_email: Optional[str] = Field(default="", alias="senderEmail")
    category: Optional[str] = None
    priority: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def sync_match_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "id" in data and "email_id" not in data and "emailId" not in data:
                data["email_id"] = data["id"]
            if "sender_name" in data and "sender_email" not in data and "senderEmail" not in data:
                data["sender_email"] = data["sender_name"]
        return data


class RuleTestResponse(CamelModel):
    matched_count: int = Field(default=0, alias="matchedCount")
    sample_size: int = Field(default=0, alias="sampleSize")
    sample_matches: list[RuleTestMatchResponse] = Field(default_factory=list, alias="sampleMatches")
    matches: list[RuleTestMatchResponse] = Field(default_factory=list, alias="matches")

    @model_validator(mode="before")
    @classmethod
    def populate_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            items = data.get("sample_matches") or data.get("sampleMatches") or data.get("matches") or []
            data["sample_matches"] = items
            data["sampleMatches"] = items
            data["matches"] = items
            if "matched_count" not in data and "matchedCount" not in data:
                data["matched_count"] = len(items)
            if "sample_size" not in data and "sampleSize" not in data:
                data["sample_size"] = len(items)
        return data


class RuleExecutionLogResponse(CamelModel):
    id: str
    rule_id: str
    email_id: str
    email_subject: str
    actions_performed: list[RuleActionSchema]
    success: bool
    error_message: Optional[str] = None
    executed_at: datetime


class RuleExecutionLogListResponse(CamelModel):
    items: list[RuleExecutionLogResponse]
    total: int
    page: int
    page_size: int


class ConditionFieldSchema(CamelModel):
    field: str
    label: str
    operators: list[str]
    options: list[str] = Field(default_factory=list)
    value_type: str = Field(default="string", alias="valueType")


class ActionTypeSchema(CamelModel):
    type: str
    label: str
    has_value: bool = Field(default=False, alias="hasValue")
    value_label: Optional[str] = Field(default=None, alias="valueLabel")
    requires_value: bool = Field(default=False, alias="requiresValue")

    @model_validator(mode="before")
    @classmethod
    def sync_requires_value(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "requires_value" in data and "has_value" not in data:
                data["has_value"] = data["requires_value"]
            elif "has_value" in data and "requires_value" not in data:
                data["requires_value"] = data["has_value"]
        return data


class RuleBuilderSchemaResponse(CamelModel):
    condition_fields: list[ConditionFieldSchema] = Field(default_factory=list)
    action_types: list[ActionTypeSchema] = Field(default_factory=list)
    condition_logic_options: list[str] = Field(default_factory=lambda: ["AND", "OR"])
