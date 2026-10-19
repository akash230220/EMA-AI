# backend/tests/unit/test_schemas_common.py
"""
Tests for app.schemas.common_schema.CamelModel — the alias generator
every response schema in the app depends on to produce camelCase JSON
matching the frontend's expectations.
"""

from typing import Optional

from app.schemas.common_schema import CamelModel


class _SampleResponse(CamelModel):
    sender_name: str
    is_read: bool
    ai_summary: Optional[str] = None
    id: str


class TestCamelModelAliasing:
    def test_single_word_field_serializes_unchanged(self):
        m = _SampleResponse(sender_name="Jane", is_read=True, id="abc123")
        assert m.model_dump(by_alias=True)["id"] == "abc123"

    def test_snake_case_field_serializes_to_camel_case(self):
        m = _SampleResponse(sender_name="Jane", is_read=True, id="abc123")
        dumped = m.model_dump(by_alias=True)
        assert "senderName" in dumped
        assert "sender_name" not in dumped
        assert dumped["senderName"] == "Jane"

    def test_boolean_field_serializes_to_camel_case(self):
        m = _SampleResponse(sender_name="Jane", is_read=True, id="abc123")
        dumped = m.model_dump(by_alias=True)
        assert dumped["isRead"] is True

    def test_three_word_snake_case_field_serializes_correctly(self):
        m = _SampleResponse(sender_name="Jane", is_read=True, ai_summary="Summary text", id="abc123")
        dumped = m.model_dump(by_alias=True)
        assert dumped["aiSummary"] == "Summary text"

    def test_can_still_construct_using_snake_case_python_kwargs(self):
        # populate_by_name=True — service-layer code constructs these
        # with normal Python snake_case kwargs; only the JSON output
        # is camelCase.
        m = _SampleResponse(sender_name="Jane", is_read=False, id="xyz")
        assert m.sender_name == "Jane"
        assert m.is_read is False

    def test_can_also_construct_using_camel_case_kwargs(self):
        m = _SampleResponse.model_validate({"senderName": "Jane", "isRead": True, "id": "abc"})
        assert m.sender_name == "Jane"