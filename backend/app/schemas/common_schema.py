# backend/app/schemas/common_schema.py
"""Shared schema primitives reused across every other schema file."""

from pydantic import BaseModel, ConfigDict


class CamelModel(BaseModel):
    """
    Base for every response schema. Serializes field names as
    camelCase in JSON output (matching every frontend api/*.js
    expectation — e.g. `pageSize`, `sortBy`, `senderName`) while
    keeping snake_case as the actual Python attribute name.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda field_name: "".join(
            word.capitalize() if i else word
            for i, word in enumerate(field_name.split("_"))
        ),
        from_attributes=True,
    )


class BulkActionResponse(CamelModel):
    affected: int