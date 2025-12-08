# app/schemas/invoice.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal

class InvoiceBase(BaseModel):
    user_id: int
    subscription_id: Optional[int] = None
    amount: Decimal
    currency: str = "INR"
    status: str = "pending"
    stripe_invoice_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    invoice_url: Optional[str] = None

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceResponse(InvoiceBase):
    id: int
    created_at: datetime
    paid_at: Optional[datetime]

    class Config:
        from_attributes = True