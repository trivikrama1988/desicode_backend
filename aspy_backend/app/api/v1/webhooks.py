from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
import stripe
import hmac
import hashlib
import json
import os
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionStatus, Plan
from app.models.invoice import Invoice

router = APIRouter()

stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
razorpay_webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")


@router.post("/webhooks/stripe", tags=["Webhooks"])
async def stripe_webhook(
        request: Request,
        db: Session = Depends(get_db)
):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_webhook_secret
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session['metadata']['user_id']
        plan_id = session['metadata']['plan_id']

        user = db.query(User).filter(User.id == user_id).first()
        plan = db.query(Plan).filter(Plan.id == plan_id).first()

        if user and plan:
            subscription = Subscription(
                user_id=user.id,
                plan_id=plan.id,
                status=SubscriptionStatus.ACTIVE,
                stripe_subscription_id=session.get('subscription'),
                stripe_customer_id=session.get('customer'),
                current_period_start=datetime.utcnow(),
                current_period_end=datetime.utcnow()  # Will be updated by invoice.paid
            )
            db.add(subscription)
            db.commit()

    elif event['type'] == 'invoice.paid':
        invoice = event['data']['object']
        subscription_id = invoice.get('subscription')

        if subscription_id:
            # Update subscription period
            subscription = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == subscription_id
            ).first()

            if subscription:
                subscription.current_period_start = datetime.fromtimestamp(invoice['period_start'])
                subscription.current_period_end = datetime.fromtimestamp(invoice['period_end'])
                db.commit()

    return {"status": "success"}


@router.post("/webhooks/razorpay", tags=["Webhooks"])
async def razorpay_webhook(
        request: Request,
        db: Session = Depends(get_db)
):
    """Handle Razorpay webhook events"""
    payload = await request.body()
    sig_header = request.headers.get('x-razorpay-signature')

    if not razorpay_webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    expected_signature = hmac.new(
        razorpay_webhook_secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, sig_header):
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = json.loads(payload)
    event = data.get('event')

    if event == 'payment.captured':
        payment = data['payload']['payment']['entity']
        user_id = payment['notes'].get('user_id')
        plan_id = payment['notes'].get('plan_id')

        if user_id and plan_id:
            user = db.query(User).filter(User.id == user_id).first()
            plan = db.query(Plan).filter(Plan.id == plan_id).first()

            if user and plan:
                subscription = Subscription(
                    user_id=user.id,
                    plan_id=plan.id,
                    status=SubscriptionStatus.ACTIVE,
                    razorpay_payment_id=payment['id'],
                    current_period_start=datetime.utcnow(),
                    current_period_end=datetime.utcnow()
                )
                db.add(subscription)
                db.commit()

                invoice = Invoice(
                    user_id=user.id,
                    subscription_id=subscription.id,
                    amount=payment['amount'] / 100,
                    currency=payment['currency'],
                    status='paid',
                    razorpay_payment_id=payment['id'],
                    paid_at=datetime.fromtimestamp(payment['created_at'])
                )
                db.add(invoice)
                db.commit()

    return {"status": "success"}