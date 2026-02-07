from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.models.chat import ChatHistory
from app.models.report import AnalysisSession
from uuid import UUID
from typing import List, Optional


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_message(
        self,
        session_id: str,
        report_id: UUID,
        role: str,
        content: str,
        image_urls: Optional[List[str]] = None,
    ) -> ChatHistory:
        message = ChatHistory(
            session_id=session_id,
            report_id=report_id,
            role=role,
            content=content,
            image_urls=image_urls,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_history_by_session(self, session_id: str) -> List[ChatHistory]:
        result = await self.db.execute(
            select(ChatHistory)
            .where(ChatHistory.session_id == session_id)
            .order_by(ChatHistory.created_at.asc())
        )
        return result.scalars().all()

    async def get_history_by_report(self, report_id: UUID) -> List[ChatHistory]:
        """Fetch chat messages for the most recent session of a specific report."""
        # First, find the most recent session_id for this report
        latest_session_query = await self.db.execute(
            select(ChatHistory.session_id)
            .where(ChatHistory.report_id == report_id)
            .order_by(ChatHistory.created_at.desc())
            .limit(1)
        )
        latest_session_id = latest_session_query.scalar_one_or_none()

        if not latest_session_id:
            return []

        # Then fetch all messages for that session
        result = await self.db.execute(
            select(ChatHistory)
            .where(ChatHistory.report_id == report_id)
            .where(ChatHistory.session_id == latest_session_id)
            .order_by(ChatHistory.created_at.asc())
        )
        return result.scalars().all()

    async def get_sessions_by_report(self, report_id: UUID) -> List[dict]:
        """List all chat sessions for a report with metadata."""
        stmt = (
            select(
                ChatHistory.session_id,
                func.min(ChatHistory.created_at).label("created_at"),
                func.max(ChatHistory.created_at).label("last_active"),
            )
            .where(ChatHistory.report_id == report_id)
            .group_by(ChatHistory.session_id)
            .order_by(desc("last_active"))
        )
        result = await self.db.execute(stmt)
        sessions = result.all()

        output = []
        for session in sessions:
            # Get first user message as title
            msg_stmt = (
                select(ChatHistory.content)
                .where(ChatHistory.session_id == session.session_id)
                .where(ChatHistory.role == "user")
                .order_by(ChatHistory.created_at.asc())
                .limit(1)
            )
            msg_res = await self.db.execute(msg_stmt)
            t = msg_res.scalar_one_or_none()
            title = t[:60] + "..." if t and len(t) > 60 else (t or "New Conversation")

            output.append(
                {
                    "session_id": session.session_id,
                    "created_at": session.created_at.isoformat()
                    if session.created_at
                    else None,
                    "title": title,
                }
            )

        return output

    async def get_report_by_id(self, report_id: UUID) -> Optional[AnalysisSession]:
        result = await self.db.execute(
            select(AnalysisSession).where(AnalysisSession.id == report_id)
        )
        return result.scalar_one_or_none()
