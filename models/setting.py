# models/setting.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base

class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, unique=True)
    folder_path = Column(String(500))
    default_sheet_name = Column(String(100))
    default_starting_cell = Column(String(10))
    outlook_enabled = Column(Boolean, default=False)
    logo_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="setting")

    def __repr__(self):
        return f"<Setting for User {self.user_id}>"