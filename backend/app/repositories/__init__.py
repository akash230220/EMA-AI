"""Mongo repository layer for the AI Email OS backend."""

from app.repositories.analytics_repository import AnalyticsSnapshotRepository
from app.repositories.automation_repository import AutomationRuleRepository, RuleExecutionLogRepository
from app.repositories.base import BaseRepository
from app.repositories.copilot_repository import CopilotConversationRepository
from app.repositories.email_repository import EmailRepository
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import SessionRepository, UserRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "SessionRepository",
    "EmailRepository",
    "TaskRepository",
    "MeetingRepository",
    "AutomationRuleRepository",
    "RuleExecutionLogRepository",
    "AnalyticsSnapshotRepository",
    "CopilotConversationRepository",
]
