# models/schedule.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    schedule_name = Column(String(255))
    campaign_config = Column(Text)  # JSON config for the campaign
    frequency = Column(String(50))  # once, daily, weekly, monthly, custom
    cron_expression = Column(String(100))
    next_run = Column(DateTime)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="schedules")

    def __repr__(self):
        return f"<Schedule {self.schedule_name}>"