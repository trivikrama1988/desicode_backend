# app/api/v1/webhooks.py
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.orm import Session
import stripe
import hmac
import hashlib
import json
import os
from datetime import datetime, timedelta

from ....db.session import get_db
from ....models.user import User
from ....models.subscription import Subscription, SubscriptionStatus, Plan
from ....models.invoice import Invoice

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
razorpay_webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")


@router.post("/webhooks/stripe", tags=["Webhooks"])
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events - BACKEND ONLY"""
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

    # Handle events
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        await handle_stripe_checkout_completed(session)

    elif event['type'] == 'invoice.paid':
        invoice = event['data']['object']
        await handle_stripe_invoice_paid(invoice)

    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        await handle_stripe_subscription_cancelled(subscription)

    return {"status": "success"}


async def handle_stripe_checkout_completed(session):
    """Handle successful Stripe checkout"""
    db = next(get_db())
    try:
        user_id = session['metadata'].get('user_id')
        plan_id = session['metadata'].get('plan_id')

        if not user_id or not plan_id:
            return

        user = db.query(User).filter(User.id == user_id).first()
        plan = db.query(Plan).filter(Plan.id == plan_id).first()

        if user and plan:
            # Update invoice
            invoice = db.query(Invoice).filter(
                Invoice.stripe_session_id == session.id
            ).first()

            if invoice:
                invoice.status = 'paid'
                invoice.paid_at = datetime.utcnow()
                invoice.stripe_payment_intent_id = session.get('payment_intent')

            # Create or update subscription
            subscription = db.query(Subscription).filter(
                Subscription.user_id == user.id,
                Subscription.plan_id == plan.id
            ).first()

            if not subscription:
                subscription = Subscription(
                    user_id=user.id,
                    plan_id=plan.id,
                    status=SubscriptionStatus.ACTIVE,
                    stripe_subscription_id=session.get('subscription'),
                    stripe_customer_id=session.get('customer'),
                    current_period_start=datetime.utcnow(),
                    current_period_end=datetime.utcnow() + timedelta(days=30)
                )
                db.add(subscription)
            else:
                subscription.status = SubscriptionStatus.ACTIVE
                subscription.current_period_start = datetime.utcnow()
                subscription.current_period_end = datetime.utcnow() + timedelta(days=30)

            db.commit()
    finally:
        db.close()


async def handle_stripe_invoice_paid(invoice):
    """Handle Stripe invoice payment"""
    db = next(get_db())
    try:
        subscription_id = invoice.get('subscription')

        if subscription_id:
            subscription = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == subscription_id
            ).first()

            if subscription:
                subscription.current_period_start = datetime.fromtimestamp(invoice['period_start'])
                subscription.current_period_end = datetime.fromtimestamp(invoice['period_end'])
                db.commit()
    finally:
        db.close()


async def handle_stripe_subscription_cancelled(subscription):
    """Handle Stripe subscription cancellation"""
    db = next(get_db())
    try:
        stripe_subscription_id = subscription.get('id')

        if stripe_subscription_id:
            subscription = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == stripe_subscription_id
            ).first()

            if subscription:
                subscription.status = SubscriptionStatus.CANCELLED
                subscription.cancelled_at = datetime.utcnow()
                db.commit()
    finally:
        db.close()


@router.post("/webhooks/razorpay", tags=["Webhooks"])
async def razorpay_webhook(request: Request):
    """Handle Razorpay webhook events - BACKEND ONLY"""
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
        await handle_razorpay_payment_captured(data['payload']['payment']['entity'])

    elif event == 'subscription.cancelled':
        await handle_razorpay_subscription_cancelled(data['payload']['subscription']['entity'])

    return {"status": "success"}


async def handle_razorpay_payment_captured(payment):
    """Handle Razorpay payment captured"""
    db = next(get_db())
    try:
        user_id = payment['notes'].get('user_id')
        plan_id = payment['notes'].get('plan_id')

        if user_id and plan_id:
            user = db.query(User).filter(User.id == user_id).first()
            plan = db.query(Plan).filter(Plan.id == plan_id).first()

            if user and plan:
                # Update invoice
                invoice = db.query(Invoice).filter(
                    Invoice.razorpay_order_id == payment['order_id']
                ).first()

                if invoice:
                    invoice.status = 'paid'
                    invoice.paid_at = datetime.fromtimestamp(payment['created_at'])
                    invoice.razorpay_payment_id = payment['id']

                # Create or update subscription
                subscription = db.query(Subscription).filter(
                    Subscription.user_id == user.id,
                    Subscription.plan_id == plan.id
                ).first()

                if not subscription:
                    subscription = Subscription(
                        user_id=user.id,
                        plan_id=plan.id,
                        status=SubscriptionStatus.ACTIVE,
                        razorpay_payment_id=payment['id'],
                        current_period_start=datetime.utcnow(),
                        current_period_end=datetime.utcnow() + timedelta(days=30)
                    )
                    db.add(subscription)
                    if invoice:
                        invoice.subscription_id = subscription.id
                else:
                    subscription.status = SubscriptionStatus.ACTIVE
                    subscription.current_period_start = datetime.utcnow()
                    subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
                    subscription.razorpay_payment_id = payment['id']

                db.commit()
    finally:
        db.close()


async def handle_razorpay_subscription_cancelled(subscription):
    """Handle Razorpay subscription cancellation"""
    db = next(get_db())
    try:
        razorpay_subscription_id = subscription.get('id')

        if razorpay_subscription_id:
            subscription = db.query(Subscription).filter(
                Subscription.razorpay_subscription_id == razorpay_subscription_id
            ).first()

            if subscription:
                subscription.status = SubscriptionStatus.CANCELLED
                subscription.cancelled_at = datetime.utcnow()
                db.commit()
    finally:
        db.close()