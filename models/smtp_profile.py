# models/smtp_profile.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base

class SMTPProfile(Base):
    __tablename__ = "smtp_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    profile_name = Column(String(100), nullable=False)
    smtp_server = Column(String(255), nullable=False)
    smtp_port = Column(Integer, nullable=False)
    sender_email = Column(String(255), nullable=False)
    sender_name = Column(String(100))
    password = Column(String(255), nullable=False)
    use_tls = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="smtp_profiles")

    def __repr__(self):
        return f"<SMTPProfile {self.profile_name}>"