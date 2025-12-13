# app/models/invoice.py - UPDATED
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=True)  # Added
    amount = Column(Numeric(10, 2))
    currency = Column(String, default="INR")
    status = Column(String, default="pending")
    stripe_invoice_id = Column(String, nullable=True, unique=True)
    stripe_session_id = Column(String, nullable=True)  # Added
    stripe_payment_intent_id = Column(String, nullable=True)  # Added
    razorpay_order_id = Column(String, nullable=True)  # Added
    razorpay_payment_id = Column(String, nullable=True, unique=True)
    invoice_url = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    paid_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="invoices")
    subscription = relationship("Subscription", back_populates="invoices")