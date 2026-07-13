# models/mapping.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base

class Mapping(Base):
    __tablename__ = "mappings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mapping_name = Column(String(100), nullable=False)
    file_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="mappings")
    entries = relationship("MappingEntry", back_populates="mapping", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Mapping {self.mapping_name}>"


class MappingEntry(Base):
    __tablename__ = "mapping_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mapping_id = Column(Integer, ForeignKey("mappings.id"), nullable=False)
    branch_name = Column(String(255), nullable=False)
    to_recipients = Column(String(500))
    cc_recipients = Column(String(500))

    # Relationships
    mapping = relationship("Mapping", back_populates="entries")

    def __repr__(self):
        return f"<MappingEntry {self.branch_name}>"