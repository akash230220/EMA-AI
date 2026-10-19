# backend/app/utils/response_wrapper.py
"""
Response Formatting & Wrapping Utilities.

Provides standardized helper functions for formatting API responses,
pagination payloads, camelCase conversion, and JSON response wrappers.
"""

from __future__ import annotations

import re
from typing import Any, Generic, Optional, TypeVar

from fastapi.responses import JSONResponse
from pydantic import BaseModel

T = TypeVar("T")


def to_camel_case(snake_str: str) -> str:
    """Converts a snake_case string into camelCase."""
    components = snake_str.split("_")
    return components[0] + "".join(x.capitalize() for x in components[1:])


def snake_to_camel_dict(data: Any) -> Any:
    """Recursively converts all dictionary keys from snake_case to camelCase."""
    if isinstance(data, dict):
        return {to_camel_case(k): snake_to_camel_dict(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [snake_to_camel_dict(item) for item in data]
    return data


def success_response(
    data: Any = None,
    message: Optional[str] = None,
    meta: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Wraps data in a consistent top-level success structure."""
    payload: dict[str, Any] = {"success": True}
    if message:
        payload["message"] = message
    if data is not None:
        payload["data"] = snake_to_camel_dict(data) if isinstance(data, (dict, list)) else data
    if meta:
        payload["meta"] = snake_to_camel_dict(meta)
    return payload


def paginated_response(
    items: list[Any],
    total: int,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """Generates standard pagination payload matching CamelModel schemas."""
    total_pages = max(1, (total + page_size - 1) // page_size) if page_size > 0 else 1
    return {
        "items": items,
        "total": total,
        "page": page,
        "pageSize": page_size,
        "totalPages": total_pages,
        "hasMore": page < total_pages,
    }


def error_response(
    detail: str,
    status_code: int = 400,
    errors: Optional[Any] = None,
) -> JSONResponse:
    """Generates a JSONResponse for errors matching the global error shape."""
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": detail,
            "errors": errors,
        },
    )

