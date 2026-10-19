# backend/tests/integration/test_copilot_stream_endpoint.py
"""
Integration test for the SSE streaming endpoint — verifies the
Content-Type and the event framing (data: {...}\n\n ... data: [DONE]\n\n)
match exactly what frontend/src/hooks/useCopilot.js's
useCopilotChatStream() parses (splitting on "\n\n", stripping the
"data:" prefix, JSON-parsing each event, and treating the literal
string "[DONE]" as a terminal sentinel).
"""

import json
from unittest.mock import patch

import pytest


async def _fake_stream_events(**kwargs):
    """Stand-in for services/copilot_service.py's stream_chat_message() async generator."""
    yield {"type": "conversation_id", "conversationId": "conv-123"}
    yield {"type": "token", "content": "Here"}
    yield {"type": "token", "content": " are your emails."}
    yield {"type": "sources", "sources": [{"email_id": "e1", "snippet": "Q3 budget approved", "score": 0.92}]}


class TestChatStreamEndpoint:
    def test_stream_response_has_event_stream_content_type(self, authenticated_client):
        with patch(
            "app.api.v1.endpoints.copilot.stream_chat_message",
            new=lambda **kwargs: _fake_stream_events(**kwargs),
        ):
            response = authenticated_client.post(
                "/api/v1/copilot/chat/stream", json={"message": "Summarize my inbox"}
            )
        assert response.headers["content-type"].startswith("text/event-stream")

    def test_stream_body_contains_every_yielded_event_as_a_data_line(self, authenticated_client):
        with patch(
            "app.api.v1.endpoints.copilot.stream_chat_message",
            new=lambda **kwargs: _fake_stream_events(**kwargs),
        ):
            response = authenticated_client.post(
                "/api/v1/copilot/chat/stream", json={"message": "Summarize my inbox"}
            )

        raw = response.text
        events = [line for line in raw.split("\n\n") if line.startswith("data:")]
        # 4 yielded events + the terminal [DONE] sentinel
        assert len(events) == 5

    def test_stream_ends_with_done_sentinel(self, authenticated_client):
        with patch(
            "app.api.v1.endpoints.copilot.stream_chat_message",
            new=lambda **kwargs: _fake_stream_events(**kwargs),
        ):
            response = authenticated_client.post(
                "/api/v1/copilot/chat/stream", json={"message": "Summarize my inbox"}
            )
        assert response.text.strip().endswith("data: [DONE]")

    def test_each_event_line_is_valid_json_after_stripping_data_prefix(self, authenticated_client):
        with patch(
            "app.api.v1.endpoints.copilot.stream_chat_message",
            new=lambda **kwargs: _fake_stream_events(**kwargs),
        ):
            response = authenticated_client.post(
                "/api/v1/copilot/chat/stream", json={"message": "Summarize my inbox"}
            )

        lines = [line for line in response.text.split("\n\n") if line.startswith("data:")]
        for line in lines[:-1]:  # exclude the [DONE] sentinel, which is not JSON
            payload = line.removeprefix("data:").strip()
            parsed = json.loads(payload)  # should not raise
            assert "type" in parsed

    def test_token_events_preserve_content_in_order(self, authenticated_client):
        with patch(
            "app.api.v1.endpoints.copilot.stream_chat_message",
            new=lambda **kwargs: _fake_stream_events(**kwargs),
        ):
            response = authenticated_client.post(
                "/api/v1/copilot/chat/stream", json={"message": "Summarize my inbox"}
            )

        lines = [line for line in response.text.split("\n\n") if line.startswith("data:")]
        token_events = [
            json.loads(line.removeprefix("data:").strip())
            for line in lines
            if '"type": "token"' in line
        ]
        combined = "".join(e["content"] for e in token_events)
        assert combined == "Here are your emails."

    def test_missing_message_field_returns_422(self, authenticated_client):
        response = authenticated_client.post("/api/v1/copilot/chat/stream", json={})
        assert response.status_code == 422