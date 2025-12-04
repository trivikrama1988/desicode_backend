# File: create_aspy_backend.py
import os
from pathlib import Path


def create_project():
    """Create complete ASPY backend with all 18 APIs"""

    PROJECT_ROOT = "aspy_backend"

    print("🚀 Creating ASPY Backend with 18 APIs...")
    print("=" * 60)

    # Define all files with their content
    files = {
        # ========== ROOT LEVEL ==========
        "requirements.txt": """fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
python-dotenv==1.0.0
pydantic[email]==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
stripe==7.7.0
razorpay==1.3.1
python-multipart==0.0.6""",

        ".env": """# Database
DATABASE_URL=postgresql+psycopg2://sachinagarwal:12345678@localhost:5432/aspy_database

# JWT Authentication
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Stripe
STRIPE_SECRET_KEY=sk_test_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_secret_here

# Razorpay
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_razorpay_secret
RAZORPAY_WEBHOOK_SECRET=your_razorpay_webhook_secret

# App Settings
ALLOWED_ORIGINS=http://localhost:3000,https://desicodes.vercel.app""",

        # ========== APP FILES ==========
        "app/main.py": """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, users, subscriptions, payments, webhooks, billing

app = FastAPI(
    title="ASPY Backend",
    description="Subscription Management API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(subscriptions.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(webhooks.router, prefix="/api/v1")
app.include_router(billing.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "ASPY Backend API", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}""",

        # ========== DB FILES ==========
        "app/db/base.py": """from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()""",

        "app/db/session.py": """from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()""",

        # ========== CORE FILES ==========
        "app/core/security.py": """from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import os
from app.db.session import get_db
from app.models.user import User

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user""",

        # ========== MODELS ==========
        "app/models/user.py": """from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    stripe_customer_id = Column(String(100), nullable=True)
    razorpay_customer_id = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    subscriptions = relationship("Subscription", back_populates="user")
    invoices = relationship("Invoice", back_populates="user")""",

        "app/models/subscription.py": """from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum

class PlanType(enum.Enum):
    FREE = "free"
    PRO = "pro"
    TEAM = "team"
    CAMPUS = "campus"

class SubscriptionStatus(enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PAST_DUE = "past_due"

class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    type = Column(SQLEnum(PlanType), unique=True)
    price = Column(Integer)
    currency = Column(String, default="INR")
    features = Column(String)
    stripe_price_id = Column(String, nullable=True)
    razorpay_plan_id = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    subscriptions = relationship("Subscription", back_populates="plan")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_id = Column(Integer, ForeignKey("plans.id"))
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    stripe_subscription_id = Column(String, nullable=True, unique=True)
    razorpay_subscription_id = Column(String, nullable=True, unique=True)
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    cancelled_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    invoices = relationship("Invoice", back_populates="subscription")""",

        "app/models/invoice.py": """from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    amount = Column(Numeric(10, 2))
    currency = Column(String, default="INR")
    status = Column(String, default="pending")
    stripe_invoice_id = Column(String, nullable=True, unique=True)
    razorpay_payment_id = Column(String, nullable=True, unique=True)
    invoice_url = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    paid_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="invoices")
    subscription = relationship("Subscription", back_populates="invoices")""",

        # ========== SCHEMAS ==========
        "app/schemas/user.py": """from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    username: str
    email: EmailStr""",

        "app/schemas/subscription.py": """from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.subscription import PlanType, SubscriptionStatus

class PlanBase(BaseModel):
    name: str
    type: PlanType
    price: int
    currency: str = "INR"
    features: str

class Plan(PlanBase):
    id: int

    class Config:
        from_attributes = True

class SubscriptionBase(BaseModel):
    plan_id: int

class SubscriptionCreate(SubscriptionBase):
    pass

class Subscription(SubscriptionBase):
    id: int
    user_id: int
    status: SubscriptionStatus
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    created_at: datetime
    cancelled_at: Optional[datetime] = None
    plan: Plan

    class Config:
        from_attributes = True""",

        "app/schemas/payment.py": """from pydantic import BaseModel
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

    class Config:
        from_attributes = True""",

        "app/schemas/billing.py": """from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class InvoiceResponse(BaseModel):
    id: int
    amount: float
    currency: str
    status: str
    created_at: datetime
    paid_at: Optional[datetime] = None
    invoice_url: Optional[str] = None

    class Config:
        from_attributes = True

class UsageStats(BaseModel):
    current_plan: str
    plan_type: str
    total_spent: float
    next_billing_date: Optional[datetime] = None
    usage_metrics: Dict[str, float]""",

        # ========== API ROUTES ==========
        "app/api/v1/auth.py": """from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.db.session import get_db

router = APIRouter(tags=["Authentication"])

@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(request: UserCreate, db: Session = Depends(get_db)):
    user_exists = db.query(User).filter(User.email == request.email).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        username=request.username,
        email=request.email,
        password=hash_password(request.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/auth/login")
def login_user(request: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()

    if not user or not verify_password(request.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid Credentials")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    token = create_access_token({"sub": user.email})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }

@router.get("/auth/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user""",

        "app/api/v1/users.py": """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.user import UserResponse, UserProfileUpdate
from app.models.user import User
from app.core.security import get_current_user
from app.db.session import get_db

router = APIRouter(tags=["Users"])

@router.get("/users/profile", response_model=UserResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/users/profile", response_model=UserResponse)
def update_user_profile(
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == current_user.id).first()

    if profile_data.email != user.email:
        existing_user = db.query(User).filter(User.email == profile_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

    user.username = profile_data.username
    user.email = profile_data.email
    db.commit()
    db.refresh(user)
    return user""",

        "app/api/v1/subscriptions.py": """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.user import User
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    subscriptions = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).all()
    return subscriptions

@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionSchema)
def get_subscription_details(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
        status=SubscriptionStatus.ACTIVE
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return subscription

@router.put("/subscriptions/{subscription_id}/cancel", response_model=SubscriptionSchema)
def cancel_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
    return plans""",

        "app/api/v1/payments.py": """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import stripe
import razorpay
import os
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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

    return history""",

        "app/api/v1/webhooks.py": """from fastapi import APIRouter, Request, HTTPException, Depends
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

router = APIRouter(tags=["Webhooks"])

stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
razorpay_webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
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
                stripe_subscription_id=session.get('subscription')
            )
            db.add(subscription)
            db.commit()

            invoice = Invoice(
                user_id=user.id,
                subscription_id=subscription.id,
                amount=plan.price / 100,
                currency=plan.currency,
                status='paid',
                stripe_invoice_id=session.get('invoice'),
                paid_at=datetime.utcnow()
            )
            db.add(invoice)
            db.commit()

    return {"status": "success"}

@router.post("/webhooks/razorpay")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    payload = await request.body()
    sig_header = request.headers.get('x-razorpay-signature')

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
                    razorpay_subscription_id=payment.get('subscription_id')
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

    return {"status": "success"}""",

        "app/api/v1/billing.py": """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.user import User
from app.models.invoice import Invoice
from app.models.subscription import Subscription, SubscriptionStatus
from app.schemas.billing import InvoiceResponse, UsageStats
from app.core.security import get_current_user

router = APIRouter(tags=["Billing"])

@router.get("/billing/invoices", response_model=List[InvoiceResponse])
def get_invoices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    invoices = db.query(Invoice).filter(
        Invoice.user_id == current_user.id
    ).order_by(Invoice.created_at.desc()).all()

    return invoices

@router.get("/billing/invoices/{invoice_id}")
def download_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user.id
    ).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.invoice_url:
        return {"download_url": invoice.invoice_url}

    raise HTTPException(status_code=404, detail="Invoice file not available")

@router.get("/billing/usage", response_model=UsageStats)
def get_usage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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
    )""",

        # ========== ALEMBIC FILES ==========
        "alembic.ini": """[alembic]
script_location = alembic

sqlalchemy.url = postgresql+psycopg2://sachinagarwal:12345678@localhost:5432/aspy_database

[post_write_hooks]
hooks = black

[loggers]
keys = root

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S""",

        "alembic/env.py": """import sys
from pathlib import Path
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.base import Base
from app.models.user import User
from app.models.subscription import Plan, Subscription
from app.models.invoice import Invoice

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    '''Run migrations in 'offline' mode.'''
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    '''Run migrations in 'online' mode.''
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()""",

        "alembic/script.py.mako": """\"\"\"${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

\"\"\"
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}""",

        "seed_plans.py": """import sys
import os
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.subscription import Plan, PlanType

def seed_plans():
    db = SessionLocal()

    plans = [
        {
            "name": "Free",
            "type": PlanType.FREE,
            "price": 0,
            "currency": "INR",
            "features": '{"projects": 1, "storage": "100MB", "support": "Community"}'
        },
        {
            "name": "Pro",
            "type": PlanType.PRO,
            "price": 49900,
            "currency": "INR",
            "features": '{"projects": 10, "storage": "10GB", "support": "Priority Email", "api_access": true}'
        },
        {
            "name": "Team",
            "type": PlanType.TEAM,
            "price": 99900,
            "currency": "INR",
            "features": '{"projects": 50, "storage": "50GB", "support": "24/7 Phone", "team_members": 10, "api_access": true}'
        },
        {
            "name": "Campus",
            "type": PlanType.CAMPUS,
            "price": 249900,
            "currency": "INR",
            "features": '{"projects": 100, "storage": "100GB", "support": "24/7 Phone", "team_members": 50, "api_access": true, "sso": true}'
        }
    ]

    for plan_data in plans:
        existing = db.query(Plan).filter(Plan.type == plan_data["type"]).first()
        if existing:
            print(f"Plan {plan_data['name']} already exists.")
            continue

        plan = Plan(**plan_data)
        db.add(plan)
        print(f"Added plan {plan_data['name']}.")

    db.commit()
    db.close()
    print("Plans seeded successfully!")

if __name__ == "__main__":
    seed_plans()""",

        # ========== INIT FILES ==========
        "app/__init__.py": """# ASPY Backend""",
        "app/api/__init__.py": """# API Routes""",
        "app/api/v1/__init__.py": """# API v1 Routes""",
        "app/core/__init__.py": """# Core Utilities""",
        "app/db/__init__.py": """# Database""",
        "app/models/__init__.py": """# Models""",
        "app/schemas/__init__.py": """# Schemas""",
        "alembic/__init__.py": """# Alembic""",
        "alembic/versions/__init__.py": """# Migration versions""",
    }

    # Create all folders
    folders = [
        "app/api/v1",
        "app/core",
        "app/db",
        "app/models",
        "app/schemas",
        "alembic/versions",
    ]

    print("📁 Creating folder structure...")
    for folder in folders:
        path = Path(PROJECT_ROOT) / folder
        path.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {folder}")

    # Create all files
    print(f"\n📄 Creating {len(files)} files...")
    for file_path, content in files.items():
        full_path = Path(PROJECT_ROOT) / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  Created: {file_path}")

    # Create initial migration
    print("\n📦 Creating initial migration...")

    migration_content = '''"""initial

Revision ID: initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=200), nullable=False),
        sa.Column('password', sa.String(length=255), nullable=False),
        sa.Column('stripe_customer_id', sa.String(length=100), nullable=True),
        sa.Column('razorpay_customer_id', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('is_superuser', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create plans table
    op.create_table('plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.Enum('FREE', 'PRO', 'TEAM', 'CAMPUS', name='plantype'), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(), server_default='INR', nullable=True),
        sa.Column('features', sa.String(), nullable=True),
        sa.Column('stripe_price_id', sa.String(), nullable=True),
        sa.Column('razorpay_plan_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('type')
    )
    op.create_index(op.f('ix_plans_id'), 'plans', ['id'], unique=False)
    op.create_index(op.f('ix_plans_name'), 'plans', ['name'], unique=True)

    # Create subscriptions table
    op.create_table('subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'CANCELLED', 'EXPIRED', 'PAST_DUE', name='subscriptionstatus'), server_default='ACTIVE', nullable=True),
        sa.Column('stripe_subscription_id', sa.String(), nullable=True, unique=True),
        sa.Column('razorpay_subscription_id', sa.String(), nullable=True, unique=True),
        sa.Column('current_period_start', sa.DateTime(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscriptions_id'), 'subscriptions', ['id'], unique=False)

    # Create invoices table
    op.create_table('invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(), server_default='INR', nullable=True),
        sa.Column('status', sa.String(), server_default='pending', nullable=True),
        sa.Column('stripe_invoice_id', sa.String(), nullable=True, unique=True),
        sa.Column('razorpay_payment_id', sa.String(), nullable=True, unique=True),
        sa.Column('invoice_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoices_id'), 'invoices', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_invoices_id'), table_name='invoices')
    op.drop_table('invoices')
    op.drop_index(op.f('ix_subscriptions_id'), table_name='subscriptions')
    op.drop_table('subscriptions')
    op.drop_index(op.f('ix_plans_name'), table_name='plans')
    op.drop_index(op.f('ix_plans_id'), table_name='plans')
    op.drop_table('plans')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.execute('DROP TYPE subscriptionstatus')
    op.execute('DROP TYPE plantype')'''

    migration_path = Path(PROJECT_ROOT) / "alembic" / "versions" / "initial_migration.py"
    migration_path.parent.mkdir(parents=True, exist_ok=True)
    migration_path.write_text(migration_content)
    print(f"  Created: alembic/versions/initial_migration.py")

    print("\n" + "=" * 60)
    print("✅ PROJECT CREATED SUCCESSFULLY!")
    print("=" * 60)

    print("\n📋 COMPLETE SETUP INSTRUCTIONS:")
    print(f"cd {PROJECT_ROOT}")
    print("pip install -r requirements.txt")
    print("alembic upgrade head")
    print("python seed_plans.py")
    print("uvicorn app.main:app --reload")

    print("\n🌐 SERVER: http://localhost:8000")
    print("📚 DOCS: http://localhost:8000/docs")

    print("\n✅ ALL 18 APIs READY:")
    print("1. POST /api/v1/auth/register")
    print("2. POST /api/v1/auth/login")
    print("3. GET  /api/v1/auth/me")
    print("4. GET  /api/v1/subscriptions")
    print("5. GET  /api/v1/subscriptions/{id}")
    print("6. POST /api/v1/subscriptions/create")
    print("7. PUT  /api/v1/subscriptions/{id}/cancel")
    print("8. GET  /api/v1/plans")
    print("9. POST /api/v1/payments/stripe/create-checkout")
    print("10. POST /api/v1/payments/razorpay/create-order")
    print("11. POST /api/v1/payments/razorpay/verify")
    print("12. GET  /api/v1/payments/history")
    print("13. POST /api/v1/webhooks/stripe")
    print("14. POST /api/v1/webhooks/razorpay")
    print("15. GET  /api/v1/billing/invoices")
    print("16. GET  /api/v1/billing/invoices/{id}")
    print("17. GET  /api/v1/billing/usage")
    print("18. GET  /api/v1/users/profile")
    print("19. PUT  /api/v1/users/profile")


if __name__ == "__main__":
    v=str(Path(__file__).parent
          )
    print(v)