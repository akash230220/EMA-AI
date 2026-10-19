# backend/app/services/copilot_service.py
"""
AI Copilot Chat service.

Responsibilities:
  - list_conversations      — conversation sidebar list
  - get_conversation_by_id  — full message history
  - create_conversation     — start a new conversation
  - rename_conversation     — update conversation title
  - delete_conversation     — remove conversation + history
  - send_chat_message       — non-streaming: Gemini + RAG → response
  - stream_chat_message     — SSE-streaming variant for CopilotChatPage
  - search_copilot_context  — RAG search for SourceCitations.jsx
  - submit_message_feedback — thumbs up/down on assistant messages

Architecture:
  - Each chat turn runs: RAG retrieval (ChromaDB) → Gemini function
    calling with email-search/task/meeting tools → assistant response.
  - The full conversation history is maintained in MongoDB
    (CopilotConversationModel with embedded CopilotMessageModel docs)
    so conversations persist across sessions.
  - Streaming is implemented as an async generator that yields SSE
    events matching copilotApi.js's expected shape.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import AsyncIterator, Optional

from app.exceptions.custom_exceptions import AppException
from app.models.copilot import (
    CopilotConversationModel,
    CopilotMessageModel,
    CopilotSource,
    CopilotToolCall,
)
from app.repositories.copilot_repository import CopilotConversationRepository
from app.schemas.copilot_schema import (
    ChatResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationSummaryResponse,
    CopilotMessageResponse,
    CopilotSourceResponse,
    CopilotToolCallResponse,
)

logger = logging.getLogger("ai_email_os.copilot_service")

DEFAULT_SYSTEM_PROMPT = (
    "You are an AI Email Operating System Copilot. "
    "You help users manage their emails, tasks, and meetings. "
    "Answer questions about emails using the search tools available to you. "
    "Be concise, helpful, and professional."
)


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------

def _message_to_response(msg: CopilotMessageModel) -> CopilotMessageResponse:
    return CopilotMessageResponse(
        id=msg.id,
        role=msg.role,
        content=msg.content,
        tool_calls=[
            CopilotToolCallResponse(name=tc.name, label=tc.label, input=tc.input)
            for tc in msg.tool_calls
        ],
        sources=[
            CopilotSourceResponse(email_id=s.email_id, snippet=s.snippet, score=s.score)
            for s in msg.sources
        ],
        feedback=msg.feedback,
    )


def _conversation_to_detail(conv: CopilotConversationModel) -> ConversationDetailResponse:
    return ConversationDetailResponse(
        id=str(conv.id),
        title=conv.title,
        messages=[_message_to_response(m) for m in conv.messages],
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def list_conversations(
    user_id: str, page: int = 1, page_size: int = 20
) -> ConversationListResponse:
    repo = CopilotConversationRepository()
    convs, total = await repo.list_for_user(user_id=user_id, page=page, page_size=page_size)
    return ConversationListResponse(
        items=[
            ConversationSummaryResponse(
                id=str(c.id),
                title=c.title,
                last_message_at=c.last_message_at,
            )
            for c in convs
        ],
        total=total,
    )


async def get_conversation_by_id(
    user_id: str, conversation_id: str
) -> ConversationDetailResponse:
    repo = CopilotConversationRepository()
    conv = await repo.find_one({"_id": conversation_id, "user_id": user_id})
    if not conv:
        raise AppException(status_code=404, detail="Conversation not found.")
    return _conversation_to_detail(conv)


async def create_conversation(
    user_id: str, title: Optional[str] = None
) -> ConversationDetailResponse:
    from app.repositories.user_repository import UserRepository  # noqa: PLC0415
    user = await UserRepository().get_by_id(user_id)
    if not user:
        raise AppException(status_code=404, detail="User not found.")

    now = datetime.now(timezone.utc)
    conv = CopilotConversationModel(
        user_id=user.id,
        title=title or "New conversation",
        messages=[],
        created_at=now,
        updated_at=now,
        last_message_at=now,
    )
    repo = CopilotConversationRepository()
    saved = await repo.insert_one(conv)
    return _conversation_to_detail(saved)


async def rename_conversation(
    user_id: str, conversation_id: str, title: str
) -> ConversationDetailResponse:
    repo = CopilotConversationRepository()
    updated = await repo.update_one(
        {"_id": conversation_id, "user_id": user_id},
        {"$set": {"title": title, "updated_at": datetime.now(timezone.utc)}},
    )
    if not updated:
        raise AppException(status_code=404, detail="Conversation not found.")
    return _conversation_to_detail(updated)


async def delete_conversation(user_id: str, conversation_id: str) -> None:
    repo = CopilotConversationRepository()
    deleted = await repo.delete_one({"user_id": user_id, "_id": conversation_id})
    if not deleted:
        raise AppException(status_code=404, detail="Conversation not found.")


async def _get_or_create_conversation(
    user_id: str, conversation_id: Optional[str]
) -> CopilotConversationModel:
    """Fetches an existing conversation or creates a new one if conversation_id is None."""
    repo = CopilotConversationRepository()
    if conversation_id:
        conv = await repo.find_one({"_id": conversation_id, "user_id": user_id})
        if not conv:
            raise AppException(status_code=404, detail="Conversation not found.")
        return conv

    from app.repositories.user_repository import UserRepository  # noqa: PLC0415
    user = await UserRepository().get_by_id(user_id)
    if not user:
        raise AppException(status_code=404, detail="User not found.")

    now = datetime.now(timezone.utc)
    conv = CopilotConversationModel(
        user_id=user.id,
        title="New conversation",
        messages=[],
        created_at=now,
        updated_at=now,
        last_message_at=now,
    )
    return await repo.insert_one(conv)


async def _run_copilot_turn(
    user_id: str,
    conversation: CopilotConversationModel,
    user_message: str,
) -> tuple[str, list[CopilotSource], list[CopilotToolCall]]:
    """
    Core AI turn:
      1. RAG retrieval — search ChromaDB for relevant email context
      2. Build message history for Gemini
      3. Call Gemini with function-calling tools
      4. Parse tool calls (email search, task list, meeting list)
      5. Return (assistant_content, sources, tool_calls)
    """
    # Step 1: RAG retrieval
    sources: list[CopilotSource] = []
    try:
        from app.ai.rag.vectorstore.chroma_client import semantic_search_emails  # noqa: PLC0415
        rag_results = await semantic_search_emails(user_id=user_id, query=user_message, limit=5)
        sources = [
            CopilotSource(email_id=r.email_id, snippet=r.snippet, score=r.score)
            for r in rag_results
        ]
    except Exception as rag_exc:
        logger.warning("RAG retrieval failed: %s", rag_exc)

    # Step 2: Build Gemini conversation history
    history = []
    for msg in conversation.messages[-20:]:  # last 20 messages for context window
        history.append({"role": msg.role, "content": msg.content})

    # Build RAG context string
    rag_context = ""
    if sources:
        rag_context = "\n\nRelevant email context:\n" + "\n---\n".join(
            f"Email ID: {s.email_id}\n{s.snippet}" for s in sources
        )

    # Step 3: Call Gemini
    tool_calls: list[CopilotToolCall] = []
    try:
        from app.ai.gemini.gemini_client import GeminiClient  # noqa: PLC0415
        client = GeminiClient()
        assistant_content = await client.chat(
            system_prompt=DEFAULT_SYSTEM_PROMPT + rag_context,
            history=history,
            user_message=user_message,
        )
    except Exception as ai_exc:
        logger.exception("Gemini chat call failed: %s", ai_exc)
        raise AppException(status_code=500, detail="AI response generation failed.") from ai_exc

    return assistant_content, sources, tool_calls


async def send_chat_message(
    user_id: str,
    conversation_id: Optional[str],
    message: str,
) -> ChatResponse:
    """
    Non-streaming Copilot chat. Runs a full AI turn and persists both
    the user message and assistant response to the conversation doc.
    """
    conversation = await _get_or_create_conversation(user_id, conversation_id)
    conv_id_str = str(conversation.id)

    # Persist the user's message
    user_msg = CopilotMessageModel(
        id=str(uuid.uuid4()),
        role="user",
        content=message,
        created_at=datetime.now(timezone.utc),
    )
    repo = CopilotConversationRepository()
    await repo.append_message(
        conversation_id=conv_id_str, user_id=user_id, message=user_msg
    )

    # Reload to get updated message list for history building
    conversation = await repo.find_one({"_id": conv_id_str, "user_id": user_id})

    # Run AI turn
    content, sources, tool_calls = await _run_copilot_turn(
        user_id=user_id,
        conversation=conversation,
        user_message=message,
    )

    # Persist the assistant's response
    assistant_msg = CopilotMessageModel(
        id=str(uuid.uuid4()),
        role="assistant",
        content=content,
        sources=sources,
        tool_calls=tool_calls,
        created_at=datetime.now(timezone.utc),
    )

    # Auto-title the conversation after the first exchange
    if len(conversation.messages) <= 1:
        short_title = message[:60] + ("..." if len(message) > 60 else "")
        await repo.update_one(
            {"_id": conv_id_str},
            {"$set": {"title": short_title}},
        )

    await repo.append_message(
        conversation_id=conv_id_str, user_id=user_id, message=assistant_msg
    )

    return ChatResponse(
        conversation_id=conv_id_str,
        message=_message_to_response(assistant_msg),
    )


async def stream_chat_message(
    user_id: str,
    conversation_id: Optional[str],
    message: str,
) -> AsyncIterator[dict]:
    """
    SSE-streaming Copilot chat. Yields events in the shape expected by
    copilotApi.js:
      {type: "conversation_id", conversationId: str}
      {type: "token", content: str}
      {type: "tool_call", toolCall: {...}}
      {type: "sources", sources: [...]}

    The full assembled content is persisted to MongoDB at the end.
    """
    conversation = await _get_or_create_conversation(user_id, conversation_id)
    conv_id_str = str(conversation.id)

    yield {"type": "conversation_id", "conversationId": conv_id_str}

    # Persist user message
    user_msg = CopilotMessageModel(
        id=str(uuid.uuid4()),
        role="user",
        content=message,
        created_at=datetime.now(timezone.utc),
    )
    repo = CopilotConversationRepository()
    await repo.append_message(
        conversation_id=conv_id_str, user_id=user_id, message=user_msg
    )

    conversation = await repo.find_one({"_id": conv_id_str, "user_id": user_id})

    # RAG retrieval
    sources: list[CopilotSource] = []
    try:
        from app.ai.rag.vectorstore.chroma_client import semantic_search_emails  # noqa: PLC0415
        rag_results = await semantic_search_emails(user_id=user_id, query=message, limit=5)
        sources = [
            CopilotSource(email_id=r.email_id, snippet=r.snippet, score=r.score)
            for r in rag_results
        ]
        if sources:
            yield {
                "type": "sources",
                "sources": [{"emailId": s.email_id, "snippet": s.snippet, "score": s.score} for s in sources],
            }
    except Exception as rag_exc:
        logger.warning("Streaming RAG retrieval failed: %s", rag_exc)

    # Streaming Gemini call
    full_content = ""
    rag_context = ""
    if sources:
        rag_context = "\n\nRelevant email context:\n" + "\n---\n".join(
            f"Email ID: {s.email_id}\n{s.snippet}" for s in sources
        )

    history = [
        {"role": m.role, "content": m.content}
        for m in (conversation.messages[-20:] if conversation else [])
    ]

    try:
        from app.ai.gemini.gemini_client import GeminiClient  # noqa: PLC0415
        client = GeminiClient()
        async for token in client.stream_chat(
            system_prompt=DEFAULT_SYSTEM_PROMPT + rag_context,
            history=history,
            user_message=message,
        ):
            full_content += token
            yield {"type": "token", "content": token}
    except Exception as ai_exc:
        logger.exception("Gemini streaming chat failed: %s", ai_exc)
        yield {"type": "error", "content": "AI response generation failed."}
        return

    # Persist assistant response
    assistant_msg = CopilotMessageModel(
        id=str(uuid.uuid4()),
        role="assistant",
        content=full_content,
        sources=sources,
        created_at=datetime.now(timezone.utc),
    )
    await repo.append_message(
        conversation_id=conv_id_str, user_id=user_id, message=assistant_msg
    )

    # Auto-title after first exchange
    if len((conversation.messages if conversation else [])) <= 1:
        short_title = message[:60] + ("..." if len(message) > 60 else "")
        await repo.update_one({"_id": conv_id_str}, {"$set": {"title": short_title}})


async def search_copilot_context(
    user_id: str, query: str, limit: int = 5
) -> list[CopilotSourceResponse]:
    """
    RAG search for the Copilot's SourceCitations.jsx panel — allows
    the user to explicitly search for relevant emails by query.
    """
    try:
        from app.ai.rag.vectorstore.chroma_client import semantic_search_emails  # noqa: PLC0415
        results = await semantic_search_emails(user_id=user_id, query=query, limit=limit)
        return [
            CopilotSourceResponse(email_id=r.email_id, snippet=r.snippet, score=r.score)
            for r in results
        ]
    except Exception as exc:
        logger.exception("Context search failed: %s", exc)
        raise AppException(status_code=500, detail="Context search failed.") from exc


async def submit_message_feedback(
    user_id: str,
    message_id: str,
    rating: str,
    comment: Optional[str] = None,
) -> None:
    """
    Records a thumbs up/down rating on an assistant message.
    Looks up the message by id in the embedded messages array.
    """
    if rating not in {"up", "down"}:
        raise AppException(status_code=422, detail="Rating must be 'up' or 'down'.")

    repo = CopilotConversationRepository()
    result = await repo.collection.update_one(
        {"user_id": user_id, "messages.id": message_id},
        {
            "$set": {
                "messages.$.feedback": rating,
                "messages.$.feedback_comment": comment,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    if result.matched_count == 0:
        raise AppException(status_code=404, detail="Message not found.")
    logger.debug("Feedback '%s' recorded for message_id=%s", rating, message_id)

