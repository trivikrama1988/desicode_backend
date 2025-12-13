# app/models/code_execution.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class CodeExecution(Base):
    __tablename__ = "code_executions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    execution_id = Column(String, unique=True, index=True)
    language = Column(String, nullable=False)
    code_hash = Column(String, index=True)
    input_data = Column(Text, nullable=True)
    output = Column(Text, nullable=True)
    errors = Column(Text, nullable=True)
    transpiled_code = Column(Text, nullable=True)
    success = Column(Boolean, default=False)
    execution_time_ms = Column(Integer)
    quota_used = Column(Integer, default=1)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("User", back_populates="executions")