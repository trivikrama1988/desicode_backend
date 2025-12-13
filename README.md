# DesiCodes Backend API

A FastAPI-based backend for code execution, subscription management, and payment processing supporting multiple Indian languages.

## Features

- **Multi-language Code Execution**: Support for 7 northeastern Indian languages
- **Subscription Management**: Free and paid tiers with quota management
- **Payment Processing**: Stripe and Razorpay integration
- **User Authentication**: JWT-based secure authentication
- **Billing System**: Automated invoicing and usage tracking

## Quick Start

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Setup database tables
python setup_database.py

# Run migrations (if needed)
alembic upgrade head
```

### 3. Environment Configuration

Create a `.env` file with your configuration:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
SECRET_KEY=your-secret-key
STRIPE_SECRET_KEY=your-stripe-key
RAZORPAY_KEY_ID=your-razorpay-key
RAZORPAY_KEY_SECRET=your-razorpay-secret
```

### 4. Start the Server

```bash
cd aspy_backend
python -m uvicorn app.main:app --reload --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication (3 APIs)
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

### Subscription Management (5 APIs)
- `GET /api/plans` - Get available plans (Free/Pro/Team/Campus)
- `GET /api/subscriptions` - Get user's subscriptions
- `GET /api/subscriptions/{id}` - Get subscription details
- `POST /api/subscriptions/create` - Create new subscription
- `PUT /api/subscriptions/{id}/cancel` - Cancel subscription

### Payment Processing (4 APIs)
- `POST /api/payments/stripe/create-checkout` - Stripe checkout session
- `POST /api/payments/razorpay/create-order` - Razorpay order creation
- `POST /api/payments/razorpay/verify` - Razorpay payment verification
- `GET /api/payments/history` - Payment transaction history

### Webhooks (2 APIs)
- `POST /api/webhooks/stripe` - Stripe payment notifications
- `POST /api/webhooks/razorpay` - Razorpay payment notifications

### Billing & Invoices (3 APIs)
- `GET /api/billing/invoices` - Get user invoices
- `GET /api/billing/invoices/{id}` - Download invoice
- `GET /api/billing/usage` - Get usage statistics

### User Profile (2 APIs)
- `GET /api/users/profile` - Get user profile
- `PUT /api/users/profile` - Update user profile

### Code Execution (Bonus Feature)
- `POST /api/run` - Execute code in 7 Indian languages
- `GET /api/run/quota` - Check execution quota
- `GET /api/run/supported-languages` - List supported languages
- `GET /api/run/history` - Get execution history

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=app tests/

# Run requirements verification
python test_requirements.py

# Run API test suite
python api_test_suite.py
```

## Project Structure

```
aspy_backend/
├── .env                    # Environment configuration
├── README.md              # Project documentation
├── IMPLEMENTATION_STATUS.md # Requirements verification
├── alembic.ini           # Database migration config
├── requirements.txt      # Dependencies
├── setup_database.py     # Database setup utility
├── test_requirements.py  # Requirements verification script
├── api_test_suite.py     # API testing suite
├── alembic/              # Database migrations
│   ├── versions/         # Migration files
│   └── env.py           # Migration environment
├── app/                  # Main application
│   ├── main.py          # FastAPI application
│   ├── core/            # Core functionality
│   │   ├── api/v1/      # API endpoints (19 required APIs)
│   │   ├── database.py  # Database configuration
│   │   └── security.py  # Authentication & security
│   ├── db/              # Database layer
│   │   ├── base.py      # SQLAlchemy base
│   │   └── session.py   # Database session management
│   ├── models/          # SQLAlchemy models
│   │   ├── user.py      # User model
│   │   ├── subscription.py # Subscription & plan models
│   │   ├── invoice.py   # Invoice model
│   │   ├── code_execution.py # Code execution tracking
│   │   └── transpiler_job.py # Job queue model
│   ├── schemas/         # Pydantic schemas
│   │   ├── user.py      # User schemas
│   │   ├── subscription.py # Subscription schemas
│   │   ├── payment.py   # Payment schemas
│   │   ├── invoice.py   # Invoice schemas
│   │   ├── billing.py   # Billing schemas
│   │   └── token.py     # JWT token schemas
│   └── services/        # Business logic
│       ├── queue_service.py   # Background job queue
│       ├── queue_services.py  # Queue utilities
│       ├── transpiler_service.py # Code execution service
│       └── worker_services.py # Worker management
├── tests/               # Test suite
│   ├── conftest.py      # Test configuration
│   ├── test_auth.py     # Authentication tests
│   ├── test_endpoints.py # API endpoint tests
│   ├── test_suites.py   # Comprehensive test suite
│   ├── test_transpiler.py # Transpiler tests
│   └── archive/         # Archived tests
└── archive/             # Utility scripts
    ├── create_default_plan.py    # Plan creation utility
    ├── create_tables.py          # Table creation utility
    ├── create_test_subscriptions.py # Test data utility
    └── seed_plans.py             # Plan seeding utility
```

## Supported Languages

- Assamese
- Bengali
- Bodo
- Manipuri
- Khasi
- Garo
- Mizo

## Requirements Compliance

This implementation meets all 19 required APIs:

- **Authentication**: 3/3 APIs 
- **Subscription Management**: 5/5 APIs 
- **Payment Processing**: 4/4 APIs
- **Webhooks**: 2/2 APIs
- **Billing & Invoices**: 3/3 APIs 
- **User Profile**: 2/2 APIs 

**Total**: 19/19 APIs 

Plus bonus multi-language code execution system.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
