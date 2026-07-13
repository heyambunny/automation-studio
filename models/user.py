# models/user.py
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    VIEWER = "viewer"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    smtp_profiles = relationship("SMTPProfile", back_populates="user")
    executions = relationship("Execution", back_populates="user")
    mappings = relationship("Mapping", back_populates="user")
    templates = relationship("Template", back_populates="user")
    schedules = relationship("Schedule", back_populates="user")
    setting = relationship("Setting", back_populates="user", uselist=False)

    def __repr__(self):
        return f"<User {self.email}>"