from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.invoice import Invoice
from app.models.subscription import Subscription, SubscriptionStatus
from app.schemas.billing import InvoiceResponse, UsageStats
from app.core.security import get_current_user

router = APIRouter()

@router.get("/billing/invoices", response_model=List[InvoiceResponse], tags=["Billing"])
def get_invoices(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all invoices for current user"""
    invoices = db.query(Invoice).filter(
        Invoice.user_id == current_user.id
    ).order_by(Invoice.created_at.desc()).all()

    return invoices

@router.get("/billing/invoices/{invoice_id}", response_model=InvoiceResponse, tags=["Billing"])
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get specific invoice by ID"""
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user.id
    ).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return invoice

@router.get("/billing/usage", response_model=UsageStats, tags=["Billing"])
def get_usage_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get usage statistics for current user"""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == SubscriptionStatus.ACTIVE
    ).first()

    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")

    invoices = db.query(Invoice).filter(
        Invoice.user_id == current_user.id,
        Invoice.subscription_id == subscription.id,
        Invoice.status == 'paid'
    ).all()

    total_spent = sum(float(invoice.amount) for invoice in invoices)

    # Example usage metrics - you should implement actual tracking
    usage_metrics = {
        "api_calls": 1250,
        "storage_used_gb": 2.5,
        "projects_created": 8
    }

    return UsageStats(
        current_plan=subscription.plan.name,
        plan_type=subscription.plan.type.value,
        total_spent=total_spent,
        next_billing_date=subscription.current_period_end,
        usage_metrics=usage_metrics
    )