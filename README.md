# Desicode Backend

Minimal backend for Desicode (Python, SQLAlchemy, Alembic).

## Requirements
- Recommended Python: 3.11 or 3.12 (prebuilt wheels available for many packages)
- Windows (PowerShell)
- `pip`, `virtualenv`
- If you see build errors for `pydantic-core` or similar, either use Python 3.11/3.12 or install Rust/Cargo via `rustup` (see https://rustup.rs/).

## Quick start

1. Create and activate virtual environment (PowerShell):
   - `python -m venv .venv`
   - `.\.venv\Scripts\Activate`

2. Upgrade packaging tools:
   - `python -m pip install --upgrade pip setuptools wheel`

3. Install dependencies:
   - `pip install -r `aspy_backend/requirements.txt``

4. Configure database connection in your environment (used by `alembic` and `app.db.session`).

5. Run migrations (from project root or `aspy_backend`):
   - `cd aspy_backend`
   - `alembic upgrade head`
   - Note: avoid typos like `upgread` — correct command is `upgrade`.

6. Seed example plans:
   - `python `aspy_backend/seed_plans.py``

7. Run the app (example using Uvicorn):
   - `uvicorn app.main:app --reload --port 8000` (run from `aspy_backend` or set PYTHONPATH accordingly)

## Common troubleshooting
- Error: “Preparing metadata ... pydantic-core ... requires Rust and Cargo”
  - Solution A: Use Python 3.11/3.12 so pip can install prebuilt wheels.
  - Solution B: Install Rust toolchain: visit https://rustup.rs/ and ensure `cargo` is on `PATH`.
- To list installed Python runtimes on Windows:
  - `py --list`
- To create a venv with a specific Python version (if installed):
  - `py -3.11 -m venv .venv2`

## Project layout
- `aspy_backend/` - main backend package
  - `app/` - application code (models, api, db)
  - `alembic/`, `alembic.ini` - migrations
  - `seed_plans.py` - helper script to insert plan data
  - `requirements.txt` - Python dependencies

## Contributing
- Follow existing code style.
- Run migrations and seed data locally before creating PRs that touch models or DB schemas.

## License
- Add project license information here.
