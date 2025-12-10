from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import stripe
import razorpay
import os
from datetime import datetime, timedelta
import json

from app.db.session import get_db
from app.models.subscription import Plan, Subscription, SubscriptionStatus
from app.models.invoice import Invoice
from app.schemas.payment import (
    StripeCheckoutRequest,
    StripeCheckoutResponse,
    RazorpayOrderRequest,
    RazorpayOrderResponse,
    RazorpayVerifyRequest,
    PaymentHistory
)
from app.core.security import get_current_user

router = APIRouter()

# Initialize payment gateways
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
razorpay_client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY_ID", ""), os.getenv("RAZORPAY_KEY_SECRET", ""))
)


def format_plan_features(plan: Plan) -> str:
    """Format plan features for display"""
    try:
        if isinstance(plan.features, str):
            features_dict = json.loads(plan.features)
        else:
            features_dict = plan.features or {}

        features_list = []
        for key, value in features_dict.items():
            key_formatted = key.replace('_', ' ').title()
            if isinstance(value, bool):
                features_list.append(f"{key_formatted}: {'Yes' if value else 'No'}")
            elif isinstance(value, (int, float)):
                features_list.append(f"{key_formatted}: {value}")
            else:
                features_list.append(f"{key_formatted}: {value}")

        return " | ".join(features_list)
    except:
        return "View features for details"


@router.post("/payments/stripe/create-checkout", response_model=StripeCheckoutResponse, tags=["Payments"])
def create_stripe_checkout(
        request: StripeCheckoutRequest,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    """
    Create Stripe checkout session for subscription

    Note: Your plan prices are stored in paise (INR cents).
    Stripe expects amounts in the smallest currency unit.
    """
    # Get the plan
    plan = db.query(Plan).filter(Plan.id == request.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Check if user already has an active subscription
    existing = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == SubscriptionStatus.ACTIVE
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="User already has an active subscription")

    try:
        # Create or retrieve Stripe customer
        customer = stripe.Customer.create(
            email=current_user.email,
            name=current_user.username,
            metadata={
                "user_id": current_user.id,
                "username": current_user.username
            }
        )

        # Determine unit amount for Stripe
        # Stripe expects amount in smallest currency unit
        currency = plan.currency.upper()

        if currency == "INR":
            # Your prices are already in paise, use as-is
            unit_amount = plan.price
        elif currency in ["USD", "EUR", "GBP"]:
            # Convert to cents (assuming price is in dollars/euros)
            unit_amount = int(plan.price * 100)
        else:
            # Default: assume price is already in smallest unit
            unit_amount = plan.price

        # Format features for product description
        features_description = format_plan_features(plan)

        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': currency.lower(),
                    'product_data': {
                        'name': plan.name,
                        'description': features_description,
                        'metadata': {
                            'plan_id': str(plan.id),
                            'plan_type': plan.type
                        }
                    },
                    'unit_amount': unit_amount,
                    'recurring': {
                        'interval': 'month',
                        'interval_count': 1
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.success_url or "http://localhost:3000/success",
            cancel_url=request.cancel_url or "http://localhost:3000/cancel",
            metadata={
                'user_id': str(current_user.id),
                'plan_id': str(plan.id),
                'plan_name': plan.name,
                'username': current_user.username
            },
            subscription_data={
                'metadata': {
                    'user_id': str(current_user.id),
                    'plan_id': str(plan.id)
                }
            },
            billing_address_collection='required' if plan.price > 0 else 'auto',
            allow_promotion_codes=True
        )

        # Create pending invoice record
        invoice = Invoice(
            user_id=current_user.id,
            amount=plan.price / 100 if currency == "INR" else plan.price,  # Convert to main currency unit
            currency=currency,
            status='pending',
            stripe_session_id=session.id,
            stripe_customer_id=customer.id,
            plan_id=plan.id,
            created_at=datetime.utcnow()
        )

        db.add(invoice)
        db.commit()

        return StripeCheckoutResponse(
            checkout_url=session.url,
            session_id=session.id
        )

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/payments/razorpay/create-order", response_model=RazorpayOrderResponse, tags=["Payments"])
def create_razorpay_order(
        request: RazorpayOrderRequest,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    """
    Create Razorpay order for payment

    Note: Your plan prices are stored in paise (INR cents).
    Razorpay expects amounts in paise for INR.
    """
    # Get the plan
    plan = db.query(Plan).filter(Plan.id == request.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Check currency compatibility
    requested_currency = request.currency.upper()
    plan_currency = plan.currency.upper()

    if requested_currency != plan_currency:
        raise HTTPException(
            status_code=400,
            detail=f"Plan currency ({plan_currency}) does not match requested currency ({requested_currency})"
        )

    # Check if user already has an active subscription
    existing = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == SubscriptionStatus.ACTIVE
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="User already has an active subscription")

    try:
        # Your prices are already in paise for INR, which is perfect for Razorpay
        # For other currencies, ensure they're in smallest unit
        if requested_currency == "INR":
            amount = plan.price  # Already in paise
        else:
            # For other currencies, assume price is in main unit and convert to smallest
            amount = int(plan.price * 100)

        # Create order data
        order_data = {
            'amount': amount,
            'currency': requested_currency,
            'receipt': f'order_{current_user.id}_{int(datetime.now().timestamp())}',
            'notes': {
                'user_id': str(current_user.id),
                'username': current_user.username,
                'plan_id': str(plan.id),
                'plan_name': plan.name,
                'email': current_user.email
            },
            'payment_capture': 1  # Auto-capture payment
        }

        # Create Razorpay order
        order = razorpay_client.order.create(data=order_data)

        # Create pending invoice record
        invoice = Invoice(
            user_id=current_user.id,
            amount=amount / 100 if requested_currency == "INR" else amount / 100,  # Convert to main currency unit
            currency=requested_currency,
            status='pending',
            razorpay_order_id=order['id'],
            plan_id=plan.id,
            created_at=datetime.utcnow()
        )

        db.add(invoice)
        db.commit()

        return RazorpayOrderResponse(
            order_id=order['id'],
            amount=order['amount'],
            currency=order['currency'],
            key_id=os.getenv("RAZORPAY_KEY_ID", "")
        )

    except razorpay.errors.RazorpayError as e:
        raise HTTPException(status_code=400, detail=f"Razorpay error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/payments/razorpay/verify", tags=["Payments"])
def verify_razorpay_payment(
        request: RazorpayVerifyRequest,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    """
    Verify Razorpay payment signature and process payment
    """
    try:
        # Verify payment signature
        params_dict = {
            'razorpay_order_id': request.razorpay_order_id,
            'razorpay_payment_id': request.razorpay_payment_id,
            'razorpay_signature': request.razorpay_signature
        }

        razorpay_client.utility.verify_payment_signature(params_dict)

        # Fetch payment details from Razorpay
        payment = razorpay_client.payment.fetch(request.razorpay_payment_id)
        order = razorpay_client.order.fetch(request.razorpay_order_id)

        # Find the pending invoice
        invoice = db.query(Invoice).filter(
            Invoice.razorpay_order_id == request.razorpay_order_id,
            Invoice.user_id == current_user.id,
            Invoice.status == 'pending'
        ).first()

        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found or already processed")

        # Update invoice with payment details
        invoice.status = 'paid'
        invoice.razorpay_payment_id = request.razorpay_payment_id
        invoice.paid_at = datetime.utcnow()
        invoice.amount = float(order['amount']) / 100  # Convert paise to rupees

        # Get plan from invoice
        plan = db.query(Plan).filter(Plan.id == invoice.plan_id).first()

        if plan:
            # Create or update subscription
            subscription = db.query(Subscription).filter(
                Subscription.user_id == current_user.id,
                Subscription.plan_id == plan.id
            ).first()

            if not subscription:
                # Create new subscription
                period_start = datetime.utcnow()
                period_end = period_start + timedelta(days=30)  # Monthly subscription

                subscription = Subscription(
                    user_id=current_user.id,
                    plan_id=plan.id,
                    status=SubscriptionStatus.ACTIVE,
                    current_period_start=period_start,
                    current_period_end=period_end,
                    razorpay_payment_id=request.razorpay_payment_id,
                    razorpay_order_id=request.razorpay_order_id,
                    created_at=datetime.utcnow()
                )
                db.add(subscription)
            else:
                # Renew existing subscription
                subscription.status = SubscriptionStatus.ACTIVE
                subscription.current_period_start = datetime.utcnow()
                subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
                subscription.razorpay_payment_id = request.razorpay_payment_id
                subscription.razorpay_order_id = request.razorpay_order_id

        db.commit()

        return {
            "status": "success",
            "message": "Payment verified and processed successfully",
            "payment_id": request.razorpay_payment_id,
            "order_id": request.razorpay_order_id,
            "amount": invoice.amount,
            "currency": invoice.currency
        }

    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid payment signature")
    except razorpay.errors.RazorpayError as e:
        raise HTTPException(status_code=400, detail=f"Razorpay error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/payments/history", response_model=List[PaymentHistory], tags=["Payments"])
def get_payment_history(
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    """
    Get payment history for current user
    """
    invoices = db.query(Invoice).filter(
        Invoice.user_id == current_user.id
    ).order_by(Invoice.created_at.desc()).all()

    history = []
    for invoice in invoices:
        # Determine payment provider
        if invoice.razorpay_payment_id:
            provider = "razorpay"
        elif invoice.stripe_payment_intent_id:
            provider = "stripe"
        elif invoice.stripe_session_id:
            provider = "stripe"
        else:
            provider = "unknown"

        # Get plan name if available
        plan_name = None
        if invoice.plan_id:
            plan = db.query(Plan).filter(Plan.id == invoice.plan_id).first()
            plan_name = plan.name if plan else None

        history.append(PaymentHistory(
            id=invoice.id,
            amount=float(invoice.amount),
            currency=invoice.currency,
            status=invoice.status,
            provider=provider,
            plan_name=plan_name,
            created_at=invoice.created_at,
            paid_at=invoice.paid_at
        ))

    return history


@router.get("/payments/methods", tags=["Payments"])
def get_payment_methods():
    """
    Get available payment methods
    """
    return {
        "available_methods": [
            {
                "provider": "razorpay",
                "currencies": ["INR"],
                "supported_cards": ["visa", "mastercard", "rupay", "amex"],
                "netbanking": True,
                "upi": True,
                "wallet": True
            },
            {
                "provider": "stripe",
                "currencies": ["INR", "USD", "EUR", "GBP"],
                "supported_cards": ["visa", "mastercard", "amex", "discover"],
                "netbanking": False,
                "upi": False,
                "wallet": False
            }
        ]
    }