# app/models/transpiler_job.py - CREATE THIS FILE
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from app.db.base import Base
import enum


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TranspilerJob(Base):
    __tablename__ = "transpiler_jobs"

    id = Column(String(50), primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    language = Column(String(50), nullable=False)
    target = Column(String(50), default="python")
    code = Column(Text, nullable=False)
    code_hash = Column(String(64), index=True)
    input_data = Column(Text, nullable=True)
    status = Column(SQLEnum(JobStatus), default=JobStatus.QUEUED)

    # Timing
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Results
    transpiled_code = Column(Text, nullable=True)
    execution_output = Column(Text, nullable=True)
    errors = Column(Text, nullable=True)
    logs = Column(Text, nullable=True)

    # Metadata
    success = Column(Boolean, default=False)
    execution_time_ms = Column(Integer, nullable=True)
    timeout_seconds = Column(Integer, default=30)
    quota_used = Column(Integer, default=1)

    # For async system
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(String(500), nullable=True)
    idempotency_key = Column(String(100), nullable=True, index=True)
    meta = Column(JSON, nullable=True, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())