from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from app.models.base import Base


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        String, index=True, nullable=False
    )  # Client session ID (groups a conversation)
    report_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analysis_sessions.id"),
        index=True,
        nullable=False,
    )
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    image_urls = Column(JSON, nullable=True)  # Array of image URLs
    tool_calls = Column(JSON, nullable=True)  # Store tool calls if any
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
