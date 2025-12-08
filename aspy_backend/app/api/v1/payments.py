from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import stripe
import razorpay
import os
from datetime import datetime

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

router = APIRouter(tags=["Payments"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
razorpay_client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY_ID", ""), os.getenv("RAZORPAY_KEY_SECRET", ""))
)

@router.post("/payments/stripe/create-checkout", response_model=StripeCheckoutResponse)
def create_stripe_checkout(
    request: StripeCheckoutRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    plan = db.query(Plan).filter(Plan.id == request.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    existing = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == SubscriptionStatus.ACTIVE
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="User already has active subscription")

    try:
        customer = stripe.Customer.create(
            email=current_user.email,
            metadata={"user_id": current_user.id}
        )

        session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': plan.currency.lower(),
                    'product_data': {'name': plan.name},
                    'unit_amount': plan.price,
                    'recurring': {'interval': 'month'},
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={'user_id': current_user.id, 'plan_id': plan.id}
        )

        return StripeCheckoutResponse(
            checkout_url=session.url,
            session_id=session.id
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/payments/razorpay/create-order", response_model=RazorpayOrderResponse)
def create_razorpay_order(
    request: RazorpayOrderRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    plan = db.query(Plan).filter(Plan.id == request.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    try:
        order_data = {
            'amount': plan.price,
            'currency': request.currency,
            'receipt': f'order_{current_user.id}_{int(datetime.now().timestamp())}',
            'notes': {'user_id': current_user.id, 'plan_id': plan.id}
        }

        order = razorpay_client.order.create(data=order_data)

        return RazorpayOrderResponse(
            order_id=order['id'],
            amount=order['amount'],
            currency=order['currency'],
            key_id=os.getenv("RAZORPAY_KEY_ID", "")
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/payments/razorpay/verify")
def verify_razorpay_payment(
    request: RazorpayVerifyRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        params_dict = {
            'razorpay_order_id': request.razorpay_order_id,
            'razorpay_payment_id': request.razorpay_payment_id,
            'razorpay_signature': request.razorpay_signature
        }

        razorpay_client.utility.verify_payment_signature(params_dict)

        invoice = Invoice(
            user_id=current_user.id,
            amount=0,
            currency="INR",
            status='paid',
            razorpay_payment_id=request.razorpay_payment_id,
            paid_at=datetime.utcnow()
        )

        db.add(invoice)
        db.commit()

        return {"status": "success", "message": "Payment verified"}

    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid payment signature")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/payments/history", response_model=List[PaymentHistory])
def get_payment_history(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    invoices = db.query(Invoice).filter(
        Invoice.user_id == current_user.id
    ).order_by(Invoice.created_at.desc()).all()

    history = []
    for invoice in invoices:
        provider = "razorpay" if invoice.razorpay_payment_id else "stripe" if invoice.stripe_invoice_id else "unknown"
        history.append(PaymentHistory(
            id=invoice.id,
            amount=float(invoice.amount),
            currency=invoice.currency,
            status=invoice.status,
            provider=provider,
            created_at=invoice.created_at
        ))

    return history