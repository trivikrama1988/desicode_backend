# app/models/user.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    stripe_customer_id = Column(String(100), nullable=True)
    razorpay_customer_id = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # New fields for execution tracking
    total_code_executions = Column(Integer, default=0)
    last_execution_at = Column(DateTime, nullable=True)
    preferred_language = Column(String(50), nullable=True, default="assamese")
    webhook_url = Column(String(500), nullable=True)  # URL to send job completion webhooks

    subscriptions = relationship("Subscription", back_populates="user")
    invoices = relationship("Invoice", back_populates="user")
    # FIX: Added this line
    executions = relationship("CodeExecution", back_populates="user")