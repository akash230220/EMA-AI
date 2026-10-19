# backend/app/schemas/task_schema.py
from datetime import date, datetime
from typing import Optional

from app.schemas.common_schema import CamelModel, BulkActionResponse

__all__ = ["BulkActionResponse"]  # re-export for endpoints/tasks.py's import


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class TaskCreateRequest(CamelModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    priority: Optional[str] = None  # high | medium | low


class TaskUpdateRequest(CamelModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    priority: Optional[str] = None


class TaskStatusUpdateRequest(CamelModel):
    status: str  # pending | in_progress | completed | dismissed


class BulkStatusUpdateRequest(CamelModel):
    task_ids: list[str]
    status: str


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class TaskResponse(CamelModel):
    id: str
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    due_date_label: Optional[str] = None
    priority: Optional[str] = None
    status: str
    source: str  # ai_extracted | manual
    source_email_id: Optional[str] = None
    created_at: datetime


class TaskListResponse(CamelModel):
    items: list[TaskResponse]
    total: int
    page: int
    page_size: int


class TaskStatsResponse(CamelModel):
    total: int
    pending: int
    completed: int
    overdue: int