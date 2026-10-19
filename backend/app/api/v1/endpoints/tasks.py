# backend/app/api/v1/endpoints/tasks.py
"""
Task CRUD + status management. Maps 1:1 to frontend/src/api/taskApi.js.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.schemas.task_schema import (
    TaskListResponse,
    TaskResponse,
    TaskCreateRequest,
    TaskUpdateRequest,
    TaskStatusUpdateRequest,
    BulkStatusUpdateRequest,
    BulkActionResponse,
    TaskStatsResponse,
)
from app.services.task_service import (
    list_tasks,
    get_task_by_id,
    create_task,
    update_task,
    update_task_status,
    delete_task,
    bulk_update_task_status,
    get_task_stats,
)
from app.auth.jwt_handler import get_current_user

router = APIRouter()


@router.get("", response_model=TaskListResponse)
async def get_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200, alias="pageSize"),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    source: Optional[str] = None,
    email_id: Optional[str] = Query(None, alias="emailId"),
    due_before: Optional[str] = Query(None, alias="dueBefore"),
    sort_by: str = Query("due_date", alias="sortBy"),
    sort_order: str = Query("asc", alias="sortOrder"),
    current_user=Depends(get_current_user),
):
    return await list_tasks(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status=status,
        priority=priority,
        source=source,
        email_id=email_id,
        due_before=due_before,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/stats", response_model=TaskStatsResponse)
async def task_stats(current_user=Depends(get_current_user)):
    return await get_task_stats(user_id=current_user.id)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, current_user=Depends(get_current_user)):
    return await get_task_by_id(user_id=current_user.id, task_id=task_id)


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task_route(payload: TaskCreateRequest, current_user=Depends(get_current_user)):
    return await create_task(user_id=current_user.id, payload=payload)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task_route(task_id: str, payload: TaskUpdateRequest, current_user=Depends(get_current_user)):
    return await update_task(user_id=current_user.id, task_id=task_id, payload=payload)


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_status(task_id: str, payload: TaskStatusUpdateRequest, current_user=Depends(get_current_user)):
    return await update_task_status(user_id=current_user.id, task_id=task_id, status=payload.status)


@router.delete("/{task_id}", status_code=204)
async def delete_task_route(task_id: str, current_user=Depends(get_current_user)):
    await delete_task(user_id=current_user.id, task_id=task_id)


@router.post("/bulk/status", response_model=BulkActionResponse)
async def bulk_status(payload: BulkStatusUpdateRequest, current_user=Depends(get_current_user)):
    affected = await bulk_update_task_status(
        user_id=current_user.id, task_ids=payload.task_ids, status=payload.status
    )
    return BulkActionResponse(affected=affected)