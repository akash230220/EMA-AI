# backend/app/api/v1/endpoints/automation.py
"""
Automation rule CRUD, reordering, testing, and execution logs.
Maps 1:1 to frontend/src/api/automationApi.js.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.schemas.automation_schema import (
    RuleListResponse,
    RuleResponse,
    RuleCreateRequest,
    RuleUpdateRequest,
    RuleEnabledUpdateRequest,
    RuleReorderRequest,
    RuleTestRequest,
    RuleTestResponse,
    RuleExecutionLogListResponse,
    RuleBuilderSchemaResponse,
)
from app.services.automation_service import (
    list_rules,
    get_rule_by_id,
    create_rule,
    update_rule,
    set_rule_enabled,
    reorder_rules,
    delete_rule,
    test_rule,
    get_rule_execution_logs,
    get_rule_builder_schema,
)
from app.auth.jwt_handler import get_current_user

router = APIRouter()


@router.get("/rules", response_model=RuleListResponse)
async def get_rules(
    enabled_only: Optional[bool] = Query(None, alias="enabledOnly"),
    sort_by: str = Query("priority", alias="sortBy"),
    sort_order: str = Query("asc", alias="sortOrder"),
    current_user=Depends(get_current_user),
):
    return await list_rules(user_id=current_user.id, enabled_only=enabled_only, sort_by=sort_by, sort_order=sort_order)


@router.get("/rules/schema", response_model=RuleBuilderSchemaResponse)
async def rule_builder_schema(current_user=Depends(get_current_user)):
    """
    Returns available condition fields/operators and action types the
    RuleBuilder UI renders — keeps the frontend in sync with what the
    Automation Agent actually supports.
    """
    return await get_rule_builder_schema()


@router.post("/rules/test", response_model=RuleTestResponse)
async def test_rule_route(payload: RuleTestRequest, current_user=Depends(get_current_user)):
    """Dry-runs a rule (or draft rule) against recent emails, before the user commits it."""
    return await test_rule(
        user_id=current_user.id,
        conditions=payload.conditions,
        condition_logic=payload.condition_logic,
        sample_size=payload.sample_size,
    )


@router.post("/rules/reorder", response_model=RuleListResponse)
async def reorder_rules_route(payload: RuleReorderRequest, current_user=Depends(get_current_user)):
    return await reorder_rules(user_id=current_user.id, rules=payload.rules)


@router.get("/rules/{rule_id}", response_model=RuleResponse)
async def get_rule(rule_id: str, current_user=Depends(get_current_user)):
    return await get_rule_by_id(user_id=current_user.id, rule_id=rule_id)


@router.post("/rules", response_model=RuleResponse, status_code=201)
async def create_rule_route(payload: RuleCreateRequest, current_user=Depends(get_current_user)):
    return await create_rule(user_id=current_user.id, payload=payload)


@router.patch("/rules/{rule_id}", response_model=RuleResponse)
async def update_rule_route(rule_id: str, payload: RuleUpdateRequest, current_user=Depends(get_current_user)):
    return await update_rule(user_id=current_user.id, rule_id=rule_id, payload=payload)


@router.patch("/rules/{rule_id}/enabled", response_model=RuleResponse)
async def set_enabled(rule_id: str, payload: RuleEnabledUpdateRequest, current_user=Depends(get_current_user)):
    return await set_rule_enabled(user_id=current_user.id, rule_id=rule_id, enabled=payload.enabled)


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule_route(rule_id: str, current_user=Depends(get_current_user)):
    await delete_rule(user_id=current_user.id, rule_id=rule_id)


@router.get("/rules/{rule_id}/logs", response_model=RuleExecutionLogListResponse)
async def rule_logs(
    rule_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    current_user=Depends(get_current_user),
):
    return await get_rule_execution_logs(user_id=current_user.id, rule_id=rule_id, page=page, page_size=page_size)