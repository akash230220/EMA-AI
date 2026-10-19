# backend/app/exceptions/custom_exceptions.py
"""
Centralized Custom Exception Hierarchy for the AI Email OS Backend.

All application-specific exceptions inherit from AppException, ensuring that
main.py's global exception handler and error_handler.py consistently format
error payloads to { "detail": "...", "errors": ... } matching the frontend's
axiosClient.js interceptor expectations.
"""

from __future__ import annotations

from typing import Any, Optional


class AppException(Exception):
    """
    Base application exception for all domain and HTTP errors.
    """

    def __init__(
        self,
        status_code: int = 400,
        detail: str = "An unexpected error occurred.",
        errors: Optional[Any] = None,
    ):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        self.errors = errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "detail": self.detail,
            "errors": self.errors,
        }


# ---------------------------------------------------------------------------
# Standard HTTP Domain Exceptions
# ---------------------------------------------------------------------------

class BadRequestException(AppException):
    def __init__(self, detail: str = "Bad request.", errors: Optional[Any] = None):
        super().__init__(status_code=400, detail=detail, errors=errors)


class UnauthorizedException(AppException):
    def __init__(self, detail: str = "Unauthorized. Please log in.", errors: Optional[Any] = None):
        super().__init__(status_code=401, detail=detail, errors=errors)


class ForbiddenException(AppException):
    def __init__(self, detail: str = "Forbidden. Insufficient permissions.", errors: Optional[Any] = None):
        super().__init__(status_code=403, detail=detail, errors=errors)


class NotFoundException(AppException):
    def __init__(self, detail: str = "Resource not found.", errors: Optional[Any] = None):
        super().__init__(status_code=404, detail=detail, errors=errors)


class ConflictException(AppException):
    def __init__(self, detail: str = "Resource conflict.", errors: Optional[Any] = None):
        super().__init__(status_code=409, detail=detail, errors=errors)


class ValidationException(AppException):
    def __init__(self, detail: str = "Validation failed.", errors: Optional[Any] = None):
        super().__init__(status_code=422, detail=detail, errors=errors)


class RateLimitException(AppException):
    def __init__(self, detail: str = "Rate limit exceeded. Please try again later.", retry_after: int = 60):
        super().__init__(status_code=429, detail=detail, errors={"retry_after_seconds": retry_after})


# ---------------------------------------------------------------------------
# Integration & AI Subsystem Exceptions
# ---------------------------------------------------------------------------

class GmailIntegrationException(AppException):
    def __init__(self, detail: str = "Gmail API operation failed.", errors: Optional[Any] = None):
        super().__init__(status_code=502, detail=detail, errors=errors)


class CalendarIntegrationException(AppException):
    def __init__(self, detail: str = "Google Calendar API operation failed.", errors: Optional[Any] = None):
        super().__init__(status_code=502, detail=detail, errors=errors)


class GeminiAIException(AppException):
    def __init__(self, detail: str = "AI processing failed.", errors: Optional[Any] = None):
        super().__init__(status_code=500, detail=detail, errors=errors)


class RAGVectorStoreException(AppException):
    def __init__(self, detail: str = "Vector store operation failed.", errors: Optional[Any] = None):
        super().__init__(status_code=500, detail=detail, errors=errors)
