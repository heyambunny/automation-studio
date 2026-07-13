# models/execution.py
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database import Base
campaign_config = Column(Text)  # JSON config for the campaign

class ExecutionStatus(str, enum.Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PENDING = "pending"

class Execution(Base):
    __tablename__ = "executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    campaign_name = Column(String(255))
    status = Column(SQLEnum(ExecutionStatus), default=ExecutionStatus.PENDING)
    send_method = Column(String(50))  # smtp, outlook_send, outlook_draft
    mode = Column(String(50))  # static/static, static/ai, ai/ai
    total_emails = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="executions")
    email_logs = relationship("EmailLog", back_populates="execution", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Execution {self.campaign_name} - {self.status}>"


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(Integer, ForeignKey("executions.id"), nullable=False)
    branch_name = Column(String(255))
    recipient_to = Column(String(500))
    recipient_cc = Column(String(500))
    subject = Column(String(500))
    status = Column(String(50))  # sent, failed, draft_saved
    error_message = Column(Text)
    sent_at = Column(DateTime)

    # Relationships
    execution = relationship("Execution", back_populates="email_logs")

    def __repr__(self):
        return f"<EmailLog {self.branch_name} - {self.status}>"