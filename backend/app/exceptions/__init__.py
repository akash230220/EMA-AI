"""Custom exceptions package."""

from app.exceptions.custom_exceptions import (
    AppException,
    BadRequestException,
    CalendarIntegrationException,
    ConflictException,
    ForbiddenException,
    GeminiAIException,
    GmailIntegrationException,
    NotFoundException,
    RAGVectorStoreException,
    RateLimitException,
    UnauthorizedException,
    ValidationException,
)

__all__ = [
    "AppException",
    "BadRequestException",
    "UnauthorizedException",
    "ForbiddenException",
    "NotFoundException",
    "ConflictException",
    "ValidationException",
    "RateLimitException",
    "GmailIntegrationException",
    "CalendarIntegrationException",
    "GeminiAIException",
    "RAGVectorStoreException",
]
