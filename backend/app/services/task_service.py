# backend/app/services/task_service.py
"""
Task CRUD and statistics service.

Responsibilities:
  - list_tasks           — paginated, filtered task list (TasksPage)
  - get_task_by_id       — single task lookup
  - create_task          — manual task creation
  - update_task          — field-level update (title, description, due_date, priority)
  - update_task_status   — status transition (pending -> in_progress -> completed | dismissed)
  - delete_task          — hard delete
  - bulk_update_task_status — batch status update
  - get_task_stats       — totals/overdue counts for Dashboard StatCards

All Mongo I/O goes through TaskRepository.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Optional

from app.exceptions.custom_exceptions import AppException
from app.models.task import TaskModel
from app.repositories.task_repository import TaskRepository
from app.schemas.task_schema import (
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskStatsResponse,
    TaskUpdateRequest,
)
from app.utils.datetime_utils import format_date_label

logger = logging.getLogger("ai_email_os.task_service")

VALID_STATUSES = {"pending", "in_progress", "completed", "dismissed"}


# ---------------------------------------------------------------------------
# Mapping helper
# ---------------------------------------------------------------------------

def _to_response(task: TaskModel) -> TaskResponse:
    due_label: Optional[str] = None
    if task.due_date:
        due_label = format_date_label(task.due_date)

    return TaskResponse(
        id=str(task.id),
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        due_date_label=due_label,
        priority=task.priority,
        status=task.status,
        source=task.source,
        source_email_id=str(task.source_email_id) if task.source_email_id else None,
        created_at=task.created_at,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def list_tasks(
    user_id: str,
    *,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    source: Optional[str] = None,
    email_id: Optional[str] = None,
    due_before: Optional[str] = None,
    sort_by: str = "due_date",
    sort_order: str = "asc",
) -> TaskListResponse:
    """Returns a paginated, filtered list of tasks."""
    repo = TaskRepository()
    tasks, total = await repo.list_for_user(
        user_id=user_id,
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
    return TaskListResponse(
        items=[_to_response(t) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_task_by_id(user_id: str, task_id: str) -> TaskResponse:
    """Returns a single task by id, scoped to the requesting user."""
    repo = TaskRepository()
    task = await repo.get_for_user(user_id=user_id, task_id=task_id)
    if not task:
        raise AppException(status_code=404, detail="Task not found.")
    return _to_response(task)


async def create_task(user_id: str, payload: TaskCreateRequest) -> TaskResponse:
    """Creates a manually entered task."""
    from app.repositories.user_repository import UserRepository  # noqa: PLC0415
    user_repo = UserRepository()
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise AppException(status_code=404, detail="User not found.")

    now = datetime.now(timezone.utc)
    task = TaskModel(
        user_id=user.id,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        priority=payload.priority,
        status="pending",
        source="manual",
        created_at=now,
        updated_at=now,
    )
    repo = TaskRepository()
    saved = await repo.insert_one(task)
    logger.info("Task created: id=%s user_id=%s", saved.id, user_id)
    return _to_response(saved)


async def update_task(
    user_id: str, task_id: str, payload: TaskUpdateRequest
) -> TaskResponse:
    """Applies partial field updates to a task (title, description, due_date, priority)."""
    repo = TaskRepository()
    task = await repo.get_for_user(user_id=user_id, task_id=task_id)
    if not task:
        raise AppException(status_code=404, detail="Task not found.")

    updates: dict = {"updated_at": datetime.now(timezone.utc)}
    if payload.title is not None:
        updates["title"] = payload.title
    if payload.description is not None:
        updates["description"] = payload.description
    if payload.due_date is not None:
        updates["due_date"] = payload.due_date
    if payload.priority is not None:
        updates["priority"] = payload.priority

    updated = await repo.update_one(
        {"_id": task.id, "user_id": user_id},
        {"$set": updates},
    )
    if not updated:
        raise AppException(status_code=404, detail="Task not found.")
    return _to_response(updated)


async def update_task_status(
    user_id: str, task_id: str, status: str
) -> TaskResponse:
    """Transitions a task's status. Sets completed_at on completion."""
    if status not in VALID_STATUSES:
        raise AppException(
            status_code=422,
            detail=f"Invalid status '{status}'. Must be one of: {', '.join(VALID_STATUSES)}.",
        )

    repo = TaskRepository()
    task = await repo.get_for_user(user_id=user_id, task_id=task_id)
    if not task:
        raise AppException(status_code=404, detail="Task not found.")

    now = datetime.now(timezone.utc)
    updates: dict = {"status": status, "updated_at": now}
    if status == "completed":
        updates["completed_at"] = now

    updated = await repo.update_one(
        {"_id": task.id, "user_id": user_id},
        {"$set": updates},
    )
    if not updated:
        raise AppException(status_code=404, detail="Task not found.")
    return _to_response(updated)


async def delete_task(user_id: str, task_id: str) -> None:
    """Permanently removes a task document."""
    repo = TaskRepository()
    deleted = await repo.delete_one({"user_id": user_id, "_id": task_id})
    if not deleted:
        raise AppException(status_code=404, detail="Task not found.")


async def bulk_update_task_status(
    user_id: str, task_ids: list[str], status: str
) -> int:
    """Applies a status update to multiple tasks at once. Returns affected count."""
    if status not in VALID_STATUSES:
        raise AppException(
            status_code=422,
            detail=f"Invalid status '{status}'. Must be one of: {', '.join(VALID_STATUSES)}.",
        )

    repo = TaskRepository()
    now = datetime.now(timezone.utc)
    updates: dict = {"status": status, "updated_at": now}
    if status == "completed":
        updates["completed_at"] = now

    result = await repo.collection.update_many(
        repo._normalize_filter({"user_id": user_id, "_id": {"$in": task_ids}}),
        {"$set": updates},
    )
    return result.modified_count


async def get_task_stats(user_id: str) -> TaskStatsResponse:
    """
    Returns high-level task counts for the Dashboard StatCards:
    total, pending, completed, and overdue (past due_date, not completed).
    """
    repo = TaskRepository()

    total = await repo.count_documents({"user_id": user_id})
    pending = await repo.count_documents({"user_id": user_id, "status": "pending"})
    completed = await repo.count_documents({"user_id": user_id, "status": "completed"})

    today = date.today()
    overdue = await repo.count_documents({
        "user_id": user_id,
        "status": {"$nin": ["completed", "dismissed"]},
        "due_date": {"$lt": today},
    })

    return TaskStatsResponse(
        total=total,
        pending=pending,
        completed=completed,
        overdue=overdue,
    )

