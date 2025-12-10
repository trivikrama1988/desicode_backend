from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.subscription import Subscription, Plan, SubscriptionStatus
from app.schemas.subscription import (
    Subscription as SubscriptionSchema,
    SubscriptionCreate,
    Plan as PlanSchema
)
from app.core.security import get_current_user
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/plans", response_model=List[PlanSchema], tags=["Plans"])
def get_available_plans(db: Session = Depends(get_db)):
    """Get all available subscription plans"""
    plans = db.query(Plan).all()
    return plans

@router.get("/subscriptions", response_model=List[SubscriptionSchema], tags=["Subscriptions"])
def get_user_subscriptions(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get current user's subscriptions"""
    subscriptions = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).all()
    return subscriptions

@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionSchema, tags=["Subscriptions"])
def get_subscription_details(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get details of a specific subscription"""
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user.id
    ).first()

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    return subscription

@router.post("/subscriptions", response_model=SubscriptionSchema, tags=["Subscriptions"])
def create_subscription(
    subscription_data: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new subscription"""
    plan = db.query(Plan).filter(Plan.id == subscription_data.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    existing = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == SubscriptionStatus.ACTIVE
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="User already has active subscription")

    # Set period end to 30 days from now
    period_start = datetime.utcnow()
    period_end = period_start + timedelta(days=30)

    subscription = Subscription(
        user_id=current_user.id,
        plan_id=subscription_data.plan_id,
        status=SubscriptionStatus.ACTIVE,
        current_period_start=period_start,
        current_period_end=period_end,
        created_at=datetime.utcnow()
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return subscription

@router.put("/subscriptions/{subscription_id}/cancel", response_model=SubscriptionSchema, tags=["Subscriptions"])
def cancel_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Cancel an active subscription"""
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user.id
    ).first()

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if subscription.status != SubscriptionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Subscription is not active")

    subscription.status = SubscriptionStatus.CANCELLED
    subscription.cancelled_at = datetime.utcnow()

    db.commit()
    db.refresh(subscription)

    return subscription