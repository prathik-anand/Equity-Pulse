from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.chat import ChatHistory
from app.models.report import AnalysisSession
from uuid import UUID
from typing import List, Optional

class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_message(self, session_id: str, report_id: UUID, role: str, content: str) -> ChatHistory:
        message = ChatHistory(
            session_id=session_id,
            report_id=report_id,
            role=role,
            content=content
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

    async def get_report_by_id(self, report_id: UUID) -> Optional[AnalysisSession]:
        result = await self.db.execute(select(AnalysisSession).where(AnalysisSession.id == report_id))
        return result.scalar_one_or_none()
