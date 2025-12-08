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
from datetime import datetime

router = APIRouter(tags=["Subscriptions"])

@router.get("/subscriptions", response_model=List[SubscriptionSchema])
def get_user_subscriptions(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)  # Get user from token
):
    subscriptions = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).all()
    return subscriptions

@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionSchema)
def get_subscription_details(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user.id
    ).first()

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    return subscription

@router.post("/subscriptions/create", response_model=SubscriptionSchema)
def create_subscription(
    subscription_data: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    plan = db.query(Plan).filter(Plan.id == subscription_data.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    existing = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == SubscriptionStatus.ACTIVE
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="User already has active subscription")

    subscription = Subscription(
        user_id=current_user.id,
        plan_id=subscription_data.plan_id,
        status=SubscriptionStatus.ACTIVE,
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow()
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return subscription

@router.put("/subscriptions/{subscription_id}/cancel", response_model=SubscriptionSchema)
def cancel_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
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

@router.get("/plans", response_model=List[PlanSchema])
def get_available_plans(db: Session = Depends(get_db)):
    plans = db.query(Plan).all()
    return plans