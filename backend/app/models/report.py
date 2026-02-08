from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from app.models.base import Base


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_session_id = Column(String, index=True, nullable=True)
    ticker = Column(String, index=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    status = Column(String, default="processing")  # processing, completed, failed
    report_data = Column(JSON, nullable=True)  # Full JSON report from agents
    summary = Column(Text, nullable=True)  # Markdown summary
    logs = Column(JSON, default=[])  # Agent execution logs
