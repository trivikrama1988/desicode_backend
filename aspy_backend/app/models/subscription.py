# app/models/subscription.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum
import json


class PlanType(enum.Enum):
    FREE = "free"
    PRO = "pro"
    TEAM = "team"
    CAMPUS = "campus"


class SubscriptionStatus(enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PAST_DUE = "past_due"


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    type = Column(SQLEnum(PlanType), unique=True)
    price = Column(Integer)
    currency = Column(String, default="INR")
    features = Column(String)
    stripe_price_id = Column(String, nullable=True)
    razorpay_plan_id = Column(String, nullable=True)

    # New fields for execution quotas
    monthly_executions = Column(Integer, default=10)  # Monthly execution quota
    max_execution_time = Column(Integer, default=30)  # Max seconds per execution
    max_code_length = Column(Integer, default=10000)  # Max characters per code
    concurrent_executions = Column(Integer, default=1)  # Max concurrent executions
    api_access = Column(Boolean, default=False)  # API access for the plan
    priority_support = Column(Boolean, default=False)  # Priority support
    created_at = Column(DateTime, server_default=func.now())

    subscriptions = relationship("Subscription", back_populates="plan")

    def get_features_dict(self):
        """Parse features JSON string to dict."""
        try:
            if self.features:
                return json.loads(self.features)
        except:
            pass
        return {}

    def set_features_dict(self, features_dict):
        """Set features as JSON string."""
        self.features = json.dumps(features_dict) if features_dict else "{}"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_id = Column(Integer, ForeignKey("plans.id"))
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    stripe_subscription_id = Column(String, nullable=True, unique=True)
    razorpay_subscription_id = Column(String, nullable=True, unique=True)
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    cancelled_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # New fields for quota tracking
    executions_this_month = Column(Integer, default=0)
    total_executions = Column(Integer, default=0)
    quota_reset_date = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    invoices = relationship("Invoice", back_populates="subscription")