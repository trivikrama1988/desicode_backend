# app/schemas/billing.py
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
from decimal import Decimal

class InvoiceResponse(BaseModel):
    id: int
    amount: Decimal
    currency: str
    status: str
    created_at: datetime
    paid_at: Optional[datetime]

    class Config:
        from_attributes = True

class UsageStats(BaseModel):
    current_plan: str
    plan_type: str
    total_spent: float
    next_billing_date: Optional[datetime]
    usage_metrics: Dict[str, float]
    execution_stats: Dict[str, int]
    quota_usage: Dict[str, float]

class PlanUsage(BaseModel):
    plan_name: str
    monthly_quota: int
    used_this_month: int
    remaining_quota: int
    usage_percentage: float
    reset_date: Optional[datetime]