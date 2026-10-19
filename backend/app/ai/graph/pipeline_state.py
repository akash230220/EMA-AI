# backend/app/ai/graph/pipeline_state.py
"""
LangGraph Shared Pipeline State.

Defines the typed state schema passed between all agents/nodes in the
multi-agent email processing pipeline.
"""

from __future__ import annotations

from typing import Annotated, Any, Optional, TypedDict


def update_list(current: list[Any], new_items: list[Any]) -> list[Any]:
    """Reducer helper to accumulate lists across graph nodes."""
    return current + (new_items or [])


class EmailProcessingState(TypedDict, total=False):
    # Core identifiers
    email_id: str
    user_id: str

    # Reader outputs
    subject: str
    sender_email: str
    sender_name: Optional[str]
    thread_transcript: str
    word_count: int
    estimated_read_seconds: int

    # Classification outputs
    category: str
    category_confidence: float
    category_reasoning: str

    intent: str
    intent_confidence: float
    action_required: bool

    priority: str
    priority_score: int
    priority_reasoning: str

    sentiment: str
    sentiment_score: float
    tone_keywords: list[str]

    # Content synthesis
    summary: str
    key_points: list[str]

    # Extracted entities
    detected_tasks: list[dict[str, Any]]
    detected_meetings: list[dict[str, Any]]

    # Automation & RAG
    executed_rules: list[str]
    embedding_indexed: bool

    # Errors & metadata
    errors: Annotated[list[str], update_list]
    pipeline_version: str

