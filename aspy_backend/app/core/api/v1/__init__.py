# app/api/v1/__init__.py - CREATE THIS FILE
from fastapi import APIRouter

# Create main router
router = APIRouter()

# Import all routers
from .auth import router as auth_router
from .users import router as users_router
from .subscriptions import router as subscriptions_router
from .payments import router as payments_router
from .webhooks import router as webhooks_router
from .billing import router as billing_router
from .invoice import router as invoice_router
from .transpiler import router as transpiler_router

# Include all routers without additional prefixes — each sub-router declares its own paths
router.include_router(auth_router, tags=["Authentication"])
router.include_router(users_router, tags=["Users"])
router.include_router(subscriptions_router, tags=["Subscriptions"])
router.include_router(payments_router, tags=["Payments"])
router.include_router(webhooks_router, tags=["Webhooks"])
router.include_router(billing_router, tags=["Billing"])
router.include_router(invoice_router, tags=["Invoices"])
router.include_router(transpiler_router, tags=["Transpiler"])

# Health check endpoint at /api/v1/health (kept for completeness)
@router.get("/health")
def health_check():
    return {
        "ok": True,
        "data": {
            "status": "healthy",
            "service": "DesiCodes API",
            "version": "1.0.0",
        }
    }