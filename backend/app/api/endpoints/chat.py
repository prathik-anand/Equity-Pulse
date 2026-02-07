from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.chat import ChatService
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from typing import Optional, List

from app.repositories.chat import ChatRepository

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str  # Client Chat Session ID
    report_id: str  # Analysis Session ID
    message: str
    active_tab: Optional[str] = "Summary"
    selected_text: Optional[str] = None
    image_urls: Optional[List[str]] = None  # Array of uploaded image URLs


def get_chat_repo(db: AsyncSession = Depends(get_db)) -> ChatRepository:
    return ChatRepository(db)


def get_chat_service(repo: ChatRepository = Depends(get_chat_repo)) -> ChatService:
    return ChatService(repo)


@router.post("/send")
async def send_chat_message(
    request: ChatRequest, service: ChatService = Depends(get_chat_service)
):
    # 1. Access Report Context (Logic in Service)
    report_context = await service.get_report_context(request.report_id)
    if report_context is None:
        raise HTTPException(status_code=404, detail="Report not found")

    # 2. Save User Message with images (Logic in Service)
    await service.save_message(
        session_id=request.session_id,
        report_id=request.report_id,
        role="user",
        content=request.message,
        image_urls=request.image_urls,
    )

    # 3. Stream Response (Logic in Service)
    # The endpoint only handles the HTTP/SSE wrapper
    return EventSourceResponse(
        service.stream_chat(
            session_id=request.session_id,
            report_id=request.report_id,  # NEW: pass for history
            message=request.message,
            report_context=report_context,
            active_tab=request.active_tab,
            selected_text=request.selected_text,
            image_urls=request.image_urls,
        )
    )


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str, service: ChatService = Depends(get_chat_service)
):
    # return await service.get_history(session_id)
    # Custom response to include thoughts
    messages = await service.get_history(session_id)
    return [
        {
            "id": str(msg.id),
            "role": msg.role,
            "content": msg.content,
            "image_urls": msg.image_urls,
            "thoughts": msg.tool_calls,  # Return saved traces as thoughts
            "created_at": msg.created_at.isoformat(),
        }
        for msg in messages
    ]


@router.get("/history/report/{report_id}")
async def get_chat_history_by_report(
    report_id: str, service: ChatService = Depends(get_chat_service)
):
    """Fetch all chat messages for a specific report, ordered by created_at."""
    messages = await service.get_history_by_report(report_id)
    return [
        {
            "id": str(msg.id),
            "role": msg.role,
            "content": msg.content,
            "image_urls": msg.image_urls,
            "thoughts": msg.tool_calls,  # Return saved traces as thoughts
            "created_at": msg.created_at.isoformat(),
        }
        for msg in messages
    ]


@router.get("/sessions/{report_id}")
async def get_chat_sessions(
    report_id: str, service: ChatService = Depends(get_chat_service)
):
    """List all chat sessions for a specific report."""
    return await service.get_sessions(report_id)
