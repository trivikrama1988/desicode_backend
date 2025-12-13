# app/schemas/subscription.py - UPDATED WITH PLAN AND SUBSCRIPTION SCHEMAS
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.subscription import PlanType, SubscriptionStatus

class PlanBase(BaseModel):
    name: str
    type: PlanType
    price: int
    currency: str = "INR"
    # Allow any type for features (DB stores JSON as a string in some rows)
    features: Optional[Any] = None

class Plan(PlanBase):
    id: int
    monthly_executions: int = 10
    max_execution_time: int = 30
    max_code_length: int = 10000
    created_at: datetime

    class Config:
        from_attributes = True

class SubscriptionBase(BaseModel):
    plan_id: int

class SubscriptionCreate(SubscriptionBase):
    pass

class Subscription(SubscriptionBase):
    id: int
    user_id: int
    status: SubscriptionStatus
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    created_at: datetime
    cancelled_at: Optional[datetime] = None
    executions_this_month: int = 0
    total_executions: int = 0

    class Config:
        from_attributes = True