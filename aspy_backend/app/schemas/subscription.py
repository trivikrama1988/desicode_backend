from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.subscription import PlanType, SubscriptionStatus

class PlanBase(BaseModel):
    name: str
    type: PlanType
    price: int
    currency: str = "INR"
    features: str

class Plan(PlanBase):
    id: int

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

    class Config:
        from_attributes = True