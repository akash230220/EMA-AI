# backend/app/api/v1/endpoints/copilot.py
"""
AI Copilot Chat — conversations, non-streaming + SSE-streaming chat,
context search, and feedback. Maps 1:1 to
frontend/src/api/copilotApi.js.
"""

import json
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.schemas.copilot_schema import (
    ConversationListResponse,
    ConversationDetailResponse,
    ConversationCreateRequest,
    ConversationRenameRequest,
    ChatRequest,
    ChatResponse,
    ContextSearchRequest,
    ContextSearchResponse,
    FeedbackRequest,
)
from app.services.copilot_service import (
    list_conversations,
    get_conversation_by_id,
    create_conversation,
    rename_conversation,
    delete_conversation,
    send_chat_message,
    stream_chat_message,
    search_copilot_context,
    submit_message_feedback,
)
from app.auth.jwt_handler import get_current_user

router = APIRouter()


@router.get("/conversations", response_model=ConversationListResponse)
async def get_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    current_user=Depends(get_current_user),
):
    return await list_conversations(user_id=current_user.id, page=page, page_size=page_size)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(conversation_id: str, current_user=Depends(get_current_user)):
    return await get_conversation_by_id(user_id=current_user.id, conversation_id=conversation_id)


@router.post("/conversations", response_model=ConversationDetailResponse, status_code=201)
async def create_conversation_route(payload: ConversationCreateRequest, current_user=Depends(get_current_user)):
    return await create_conversation(user_id=current_user.id, title=payload.title)


@router.patch("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def rename_conversation_route(
    conversation_id: str, payload: ConversationRenameRequest, current_user=Depends(get_current_user)
):
    return await rename_conversation(user_id=current_user.id, conversation_id=conversation_id, title=payload.title)


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation_route(conversation_id: str, current_user=Depends(get_current_user)):
    await delete_conversation(user_id=current_user.id, conversation_id=conversation_id)


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, current_user=Depends(get_current_user)):
    """
    Non-streaming Copilot chat. Backend orchestrates Gemini function
    calling + RAG retrieval (ChromaDB) + LangGraph tool execution and
    returns the final assistant message in one response.
    """
    return await send_chat_message(
        user_id=current_user.id,
        conversation_id=payload.conversation_id,
        message=payload.message,
    )


@router.post("/chat/stream")
async def chat_stream(payload: ChatRequest, current_user=Depends(get_current_user)):
    """
    SSE-streaming variant. Emits events matching the shape expected by
    frontend's copilotApi.streamMessage() / useCopilotChatStream():
      data: {"type": "conversation_id", "conversationId": "..."}
      data: {"type": "token", "content": "..."}
      data: {"type": "tool_call", "toolCall": {...}}
      data: {"type": "sources", "sources": [...]}
      data: [DONE]
    """

    async def event_generator():
        async for event in stream_chat_message(
            user_id=current_user.id,
            conversation_id=payload.conversation_id,
            message=payload.message,
        ):
            yield f"data: {json.dumps(event)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/context/search", response_model=ContextSearchResponse)
async def context_search(payload: ContextSearchRequest, current_user=Depends(get_current_user)):
    results = await search_copilot_context(user_id=current_user.id, query=payload.query, limit=payload.limit)
    return ContextSearchResponse(results=results)


@router.post("/messages/{message_id}/feedback", status_code=204)
async def submit_feedback(message_id: str, payload: FeedbackRequest, current_user=Depends(get_current_user)):
    await submit_message_feedback(
        user_id=current_user.id, message_id=message_id, rating=payload.rating, comment=payload.comment
    )