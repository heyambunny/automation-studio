# models/user.py
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import hashlib
import os


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
    is_active = Column(String(1), default='Y')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    smtp_profiles = relationship("SMTPProfile", back_populates="user")
    executions = relationship("Execution", back_populates="user")
    mappings = relationship("Mapping", back_populates="user")
    templates = relationship("Template", back_populates="user")
    schedules = relationship("Schedule", back_populates="user")
    setting = relationship("Setting", back_populates="user", uselist=False)

    @staticmethod
    def hash_password(password: str) -> str:
        salt = os.urandom(32).hex()
        return salt + ":" + hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()

    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        salt, hash_val = stored_hash.split(":")
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex() == hash_val

    def __repr__(self):
        return f"<User {self.email}>"