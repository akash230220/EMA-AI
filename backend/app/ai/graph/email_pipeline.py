# backend/app/ai/graph/email_pipeline.py
"""
LangGraph Multi-Agent Email Processing Pipeline.

Orchestrates sequential and parallel AI agents:
  1. Reader Node: cleans & structures thread transcript
  2. Categorization Node: detects category (work, finance, etc.)
  3. Intent Node: detects intent (meeting_request, task, urgent_action, etc.)
  4. Sentiment Node: detects sentiment polarity & tone
  5. Priority Node: scores urgency using category + intent context
  6. Summarization Node: generates executive summary & key points
  7. Extraction Node: extracts tasks & calendar meetings (creates DB records)
  8. Persistence Node: writes all AI fields back to MongoDB EmailModel
  9. Automation Node: evaluates user rules & triggers automated actions
 10. RAG Indexing Node: embeds email content into ChromaDB vector store
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from app.ai.agents.automation_agent import process_automation_rules
from app.ai.agents.categorization_agent import categorize_email
from app.ai.agents.intent_agent import detect_intent
from app.ai.agents.meeting_agent import detect_meetings
from app.ai.agents.priority_agent import detect_priority
from app.ai.agents.reader_agent import read_email
from app.ai.agents.sentiment_agent import analyze_sentiment
from app.ai.agents.summarization_agent import summarize_email
from app.ai.agents.task_agent import extract_tasks
from app.ai.graph.pipeline_state import EmailProcessingState
from app.models.email import EmailModel
from app.repositories.email_repository import EmailRepository

logger = logging.getLogger("ai_email_os.email_pipeline")

PIPELINE_VERSION = "2.0.0"


# ---------------------------------------------------------------------------
# Pipeline Nodes
# ---------------------------------------------------------------------------

async def reader_node(state: EmailProcessingState) -> dict[str, Any]:
    """Reads email from MongoDB and normalizes thread content."""
    repo = EmailRepository()
    email = await repo.get_for_user(user_id=state["user_id"], email_id=state["email_id"])
    if not email:
        return {"errors": [f"Email {state['email_id']} not found."]}

    read_data = await read_email(email)
    return {
        "subject": read_data["subject"],
        "sender_email": read_data["sender_email"],
        "sender_name": read_data["sender_name"],
        "thread_transcript": read_data["thread_transcript"],
        "word_count": read_data["word_count"],
        "estimated_read_seconds": read_data["estimated_read_seconds"],
    }


async def classification_node(state: EmailProcessingState) -> dict[str, Any]:
    """Runs categorization, intent detection, and sentiment analysis concurrently."""
    transcript = state.get("thread_transcript", "")
    subject = state.get("subject", "")

    cat_task = categorize_email(subject, transcript)
    intent_task = detect_intent(subject, transcript)
    sent_task = analyze_sentiment(subject, transcript)

    cat_res, intent_res, sent_res = await asyncio.gather(
        cat_task, intent_task, sent_task, return_exceptions=True
    )

    updates: dict[str, Any] = {}

    if isinstance(cat_res, dict):
        updates["category"] = cat_res.get("category", "work")
        updates["category_confidence"] = cat_res.get("confidence", 0.9)
        updates["category_reasoning"] = cat_res.get("reasoning", "")
    else:
        updates["category"] = "work"

    if isinstance(intent_res, dict):
        updates["intent"] = intent_res.get("intent", "fyi")
        updates["intent_confidence"] = intent_res.get("confidence", 0.9)
        updates["action_required"] = intent_res.get("action_required", False)
    else:
        updates["intent"] = "fyi"

    if isinstance(sent_res, dict):
        updates["sentiment"] = sent_res.get("sentiment", "neutral")
        updates["sentiment_score"] = sent_res.get("score", 0.0)
        updates["tone_keywords"] = sent_res.get("tone_keywords", [])
    else:
        updates["sentiment"] = "neutral"

    return updates


async def priority_node(state: EmailProcessingState) -> dict[str, Any]:
    """Calculates priority score using category and intent context."""
    p_res = await detect_priority(
        subject=state.get("subject", ""),
        transcript=state.get("thread_transcript", ""),
        category=state.get("category", "work"),
        intent=state.get("intent", "fyi"),
    )
    return {
        "priority": p_res.get("priority", "medium"),
        "priority_score": p_res.get("score", 5),
        "priority_reasoning": p_res.get("reasoning", ""),
    }


async def summarization_node(state: EmailProcessingState) -> dict[str, Any]:
    """Generates executive summary and bullet points."""
    sum_res = await summarize_email(
        subject=state.get("subject", ""),
        transcript=state.get("thread_transcript", ""),
    )
    return {
        "summary": sum_res.get("summary", ""),
        "key_points": sum_res.get("key_points", []),
    }


async def extraction_node(state: EmailProcessingState) -> dict[str, Any]:
    """Extracts actionable tasks and calendar meetings."""
    subject = state.get("subject", "")
    transcript = state.get("thread_transcript", "")
    user_id = state["user_id"]
    email_id = state["email_id"]

    tasks_task = extract_tasks(subject, transcript, user_id, email_id)
    meetings_task = detect_meetings(subject, transcript, user_id, email_id)

    tasks_res, meetings_res = await asyncio.gather(
        tasks_task, meetings_task, return_exceptions=True
    )

    detected_tasks = tasks_res if isinstance(tasks_res, list) else []
    detected_meetings = meetings_res if isinstance(meetings_res, list) else []

    return {
        "detected_tasks": detected_tasks,
        "detected_meetings": detected_meetings,
    }


async def persistence_node(state: EmailProcessingState) -> dict[str, Any]:
    """Persists all computed AI fields onto the MongoDB EmailModel document."""
    repo = EmailRepository()
    now = datetime.now(timezone.utc)

    # Determine if pending_reply should be set
    intent = state.get("intent", "")
    pending_reply = intent in ("question", "meeting_request", "urgent_action")

    update_fields = {
        "category": state.get("category"),
        "priority": state.get("priority"),
        "intent": state.get("intent"),
        "sentiment": state.get("sentiment"),
        "ai_summary": state.get("summary"),
        "ai_key_points": state.get("key_points", []),
        "detected_tasks": [
            t.model_dump() if hasattr(t, "model_dump") else t
            for t in state.get("detected_tasks", [])
        ],
        "detected_meetings": [
            m.model_dump() if hasattr(m, "model_dump") else m
            for m in state.get("detected_meetings", [])
        ],
        "pending_reply": pending_reply,
        "ai_processed_at": now,
        "ai_pipeline_version": PIPELINE_VERSION,
        "updated_at": now,
    }

    await repo.update_one(
        {"_id": state["email_id"], "user_id": state["user_id"]},
        {"$set": update_fields},
    )
    logger.info("Persisted AI pipeline results for email %s", state["email_id"])
    return {}


async def automation_node(state: EmailProcessingState) -> dict[str, Any]:
    """Evaluates automation rules against the processed email."""
    repo = EmailRepository()
    email = await repo.get_for_user(user_id=state["user_id"], email_id=state["email_id"])
    if not email:
        return {}

    executed = await process_automation_rules(email=email, user_id=state["user_id"])
    return {"executed_rules": executed}


async def rag_indexing_node(state: EmailProcessingState) -> dict[str, Any]:
    """Indexes email transcript & summary into ChromaDB for semantic search."""
    try:
        from app.ai.rag.vectorstore.chroma_client import index_email  # noqa: PLC0415
        await index_email(
            email_id=state["email_id"],
            user_id=state["user_id"],
            subject=state.get("subject", ""),
            snippet=state.get("summary") or state.get("thread_transcript", "")[:300],
            body=state.get("thread_transcript", ""),
        )

        repo = EmailRepository()
        await repo.update_one(
            {"_id": state["email_id"], "user_id": state["user_id"]},
            {
                "$set": {
                    "embedding_indexed": True,
                    "embedding_indexed_at": datetime.now(timezone.utc),
                }
            },
        )
        return {"embedding_indexed": True}
    except Exception as exc:
        logger.warning("RAG indexing failed for email %s: %s", state["email_id"], exc)
        return {"embedding_indexed": False}


# ---------------------------------------------------------------------------
# LangGraph Workflow Construction
# ---------------------------------------------------------------------------

def build_email_graph():
    """
    Constructs the LangGraph StateGraph pipeline.
    Falls back gracefully if langgraph is not installed in the environment.
    """
    try:
        from langgraph.graph import END, START, StateGraph  # noqa: PLC0415

        builder = StateGraph(EmailProcessingState)

        # Add Nodes
        builder.add_node("reader", reader_node)
        builder.add_node("classification", classification_node)
        builder.add_node("priority", priority_node)
        builder.add_node("summarization", summarization_node)
        builder.add_node("extraction", extraction_node)
        builder.add_node("persistence", persistence_node)
        builder.add_node("automation", automation_node)
        builder.add_node("rag_indexing", rag_indexing_node)

        # Add Edges
        builder.add_edge(START, "reader")
        builder.add_edge("reader", "classification")
        builder.add_edge("classification", "priority")
        builder.add_edge("priority", "summarization")
        builder.add_edge("summarization", "extraction")
        builder.add_edge("extraction", "persistence")
        builder.add_edge("persistence", "automation")
        builder.add_edge("automation", "rag_indexing")
        builder.add_edge("rag_indexing", END)

        return builder.compile()
    except ImportError:
        logger.info("LangGraph native library not present; using built-in sequential orchestrator.")
        return None


_compiled_graph = None


def get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_email_graph()
    return _compiled_graph


# ---------------------------------------------------------------------------
# Main Pipeline Runner
# ---------------------------------------------------------------------------

async def run_email_pipeline(email_id: str, user_id: str) -> dict[str, Any]:
    """
    Executes the full AI email processing pipeline for a single email document.
    """
    logger.info("Starting AI pipeline execution for email_id=%s user_id=%s", email_id, user_id)

    initial_state: EmailProcessingState = {
        "email_id": email_id,
        "user_id": user_id,
        "pipeline_version": PIPELINE_VERSION,
        "errors": [],
    }

    graph = get_compiled_graph()

    if graph is not None:
        try:
            final_state = await graph.ainvoke(initial_state)
            return dict(final_state)
        except Exception as exc:
            logger.warning("LangGraph execution encountered exception: %s. Running fallback runner.", exc)

    # Built-in direct asynchronous execution flow
    state = dict(initial_state)

    r_out = await reader_node(state)  # type: ignore
    state.update(r_out)

    c_out = await classification_node(state)  # type: ignore
    state.update(c_out)

    p_out = await priority_node(state)  # type: ignore
    state.update(p_out)

    s_out = await summarization_node(state)  # type: ignore
    state.update(s_out)

    e_out = await extraction_node(state)  # type: ignore
    state.update(e_out)

    await persistence_node(state)  # type: ignore

    a_out = await automation_node(state)  # type: ignore
    state.update(a_out)

    rag_out = await rag_indexing_node(state)  # type: ignore
    state.update(rag_out)

    logger.info("AI email pipeline completed successfully for email_id=%s", email_id)
    return state

