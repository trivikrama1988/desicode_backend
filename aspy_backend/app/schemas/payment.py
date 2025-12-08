# app/schemas/payment.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class StripeCheckoutRequest(BaseModel):
    plan_id: int
    success_url: str
    cancel_url: str

class StripeCheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str

class RazorpayOrderRequest(BaseModel):
    plan_id: int
    currency: str = "INR"

class RazorpayOrderResponse(BaseModel):
    order_id: str
    amount: int
    currency: str
    key_id: str

class RazorpayVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

class PaymentHistory(BaseModel):
    id: int
    amount: float
    currency: str
    status: str
    provider: str
    created_at: datetime