# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the API router using relative imports
try:
    from .core.api.v1 import router as api_v1_router
    print("[OK] Successfully imported API router")
except ImportError as e:
    print(f"[ERROR] Failed to import API router: {e}")
    api_v1_router = None


app = FastAPI(
    title="DesiCodes Backend API",
    description="Subscription Management and Code Execution API for DesiCodes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration for DesiCodes frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://desicodes.vercel.app",
        "http://localhost:5173",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
        "Access-Control-Allow-Headers",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
        "X-API-Key",
        "X-User-ID",
        "Idempotency-Key",  # Important for idempotency
    ],
    expose_headers=["*"],
    max_age=600,
)

# Include the main API router if we found one
if api_v1_router:
    app.include_router(api_v1_router, prefix="/api")
    print("[OK] API router included with prefix /api")
else:
    print("[WARNING] API router not found, adding fallback routes")
    # Add basic fallback routes for testing
    @app.get("/api/health")
    def api_health():
        return {"status": "healthy", "message": "Fallback health endpoint"}

    @app.get("/api/plans")
    def get_plans():
        return {"message": "API router not loaded", "plans": []}

@app.get("/")
def root():
    return {
        "ok": True,
        "data": {
            "message": "DesiCodes Backend API",
            "status": "running",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/api/health",
            "endpoints": [
                "/api/auth/*",
                "/api/users/*",
                "/api/subscriptions/*",
                "/api/payments/*",
                "/api/webhooks/*",
                "/api/billing/*",
                "/api/invoices/*",
                "/api/transpiler/*"
            ]
        }
    }

@app.get("/health")
def root_health():
    return {"status": "healthy"}
