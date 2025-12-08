Here is the updated `README.md` with details matching your actual project structure:

```markdown
# DesiCode Backend

## Overview
This repository contains the backend for the DesiCode project (Python/FastAPI). This `README.md` documents setup, running, testing, debugging and troubleshooting steps for development on Windows.

[Developer Guide](`DevelopersGuide.md`)

## Table of Contents
- `Prerequisites`
- `Install dependencies`
- `Environment variables`
- `Run the backend`
- `Run tests`
- `Project structure`
- `Available test utilities`
- `How to undo git add .`
- `Troubleshooting`
- `Contributing`
- `Security`

## Prerequisites
- `Python 3.10` or newer installed
- `pip` available
- `git` installed
- The backend server must be reachable at `http://localhost:8000` for tests and integrations

## Install dependencies
From the repository root, install main requirements:
```bash
python -m pip install -r aspy_backend/requirements.txt
```

Install test and dev tools (if not already included):
```bash
python -m pip install pytest requests python-jose
```

## Environment variables
Create a `.env` file at the repo root or set environment variables in your shell. Minimum variables required:

- `SECRET_KEY` — JWT signing key used by the app
- `DATABASE_URL` — database connection string (e.g., PostgreSQL, SQLite)
- `TEST_DATABASE_URL` — optional test database

Windows (PowerShell):
```powershell
$env:SECRET_KEY = "your-secret-key-here"
$env:DATABASE_URL = "postgresql://user:password@localhost/desicode_db"
$env:TEST_DATABASE_URL = "sqlite:///./test.db"
```

Windows (Command Prompt):
```cmd
set SECRET_KEY=your-secret-key-here
set DATABASE_URL=postgresql://user:password@localhost/desicode_db
set TEST_DATABASE_URL=sqlite:///./test.db
```

Note: Prefer a `.env` file with `python-dotenv` for convenience.

## Run the backend
Start the FastAPI app:
```bash
uvicorn aspy_backend.app.main:app --reload --port 8000
```

Confirm the server is running:
- Base URL: `http://localhost:8000`
- API documentation: `http://localhost:8000/docs` (Swagger UI)
- Alternative docs: `http://localhost:8000/redoc` (ReDoc)

## Run tests
The `aspy_backend/tests/` folder contains several test utilities:


### Run specific test file
```bash
python aspy_backend/tests/test_auth.py
```

### Available test utilities
- `test_auth.py` — authentication and JWT token tests
- `test_api.py` — API endpoint tests
- `test_endpoints.py` — endpoint verification tests
- `test_suites.py` — comprehensive test suites
- `quick_test.py` — quick sanity checks
- `stress_test.py` — load/stress testing
- `admin_test.py` — admin functionality tests
- `check_seed_plan.py` — seed data validation

Run a quick test:
```bash
python aspy_backend/tests/quick_test.py
```

Run authentication debug script:
```bash
python aspy_backend/tests/test_auth.py
```

Common `pytest` flags:
- `-q` — quiet output
- `-k <expr>` — run tests matching expression
- `-x` — stop after first failure
- `--maxfail=<n>` — limit failures before stopping
- `-v` — verbose output

## Project structure
```
`desicode_backend`/
  `README.md`
  `DevelopersGuide.md`
  `aspy_backend/`
    `__init__.py`
    `requirements.txt`
    `alembic.ini`
    `seed_plans.py`
    `app/`
      `__init__.py`
      `main.py`
      `api/`
        `__init__.py`
        `v1/`
          `__init__.py`
          `auth.py`
          `users.py`
          `billing.py`
          `invoice.py`
          `payments.py`
          `subscriptions.py`
          `webhooks.py`
      `core/`
        `__init__.py`
        `security.py`
      `db/`
        `__init__.py`
        `base.py`
        `session.py`
      `models/`
        `__init__.py`
        `user.py`
        `subscription.py`
        `invoice.py`
      `schemas/`
        `__init__.py`
        `user.py`
        `billing.py`
        `invoice.py`
        `payment.py`
        `subscription.py`
    `alembic/`
      `__init__.py`
      `env.py`
      `script.py.mako`
      `versions/`
        `initial_migration.py`
    `tests/`
      `test_auth.py`
      `test_api.py`
      `test_endpoints.py`
      `test_suites.py`
      `quick_test.py`
      `stress_test.py`
      `admin_test.py`
      `check_seed_plan.py`
```

## Database migrations
Run Alembic migrations:
```bash
alembic upgrade head
```

Create a new migration:
```bash
alembic revision --autogenerate -m "migration description"
```

## API endpoints
Main API endpoints are organized by feature under `aspy_backend/app/api/v1/`:
- `/auth` — authentication (login, register, token refresh)
- `/users` — user management
- `/subscriptions` — subscription plans and management
- `/billing` — billing information
- `/invoices` — invoice generation and retrieval
- `/payments` — payment processing
- `/webhooks` — webhook handlers

See `DevelopersGuide.md` for detailed endpoint documentation.

## How to undo `git add .`
To unstage all files after running `git add .`:
```bash
git restore --staged .
```

Fallback for older Git versions:
```bash
git reset HEAD .
```

## Quick troubleshooting
- **401 on protected endpoints:**
  - Verify `SECRET_KEY` matches server
  - Confirm token not expired
  - Check server time / timezone skew

- **Database connection errors:**
  - Verify `DATABASE_URL` is correct
  - Ensure database server is running
  - Check DB credentials and permissions

- **Migration errors:**
  - Run `alembic upgrade head` to apply pending migrations
  - Check `alembic/versions/` for migration scripts

- **Import errors:**
  - Verify Python path is correct
  - Reinstall dependencies: `python -m pip install -r aspy_backend/requirements.txt`

- **Test failures:**
  - Ensure backend server is running at `http://localhost:8000`
  - Check `.env` variables are set correctly
  - Review test output for specific error messages

## Contributing
- Follow repository coding standards
- Add tests for new features or bug fixes
- Run `pytest` before opening a PR
- Keep secrets out of commits

## Security
- Never commit `SECRET_KEY` or real credentials
- Use `.env` file for local secrets (add to `.gitignore`)
- Rotate signing keys if exposed
- Review `aspy_backend/core/security.py` for authentication logic

---
Keep all secrets out of the repo and change demo values before deploying to production.
```
