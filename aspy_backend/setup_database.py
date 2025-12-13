#!/usr/bin/env python3
"""Create database tables if they don't exist."""

import sys
from sqlalchemy import create_engine, text
from app.db.base import Base
from app.models.user import User
from app.models.subscription import Plan, Subscription
from app.models.invoice import Invoice
from app.models.code_execution import CodeExecution
from app.models.transpiler_job import TranspilerJob
import os
from dotenv import load_dotenv

def create_tables():
    """Create all database tables."""

    # Load environment variables
    load_dotenv()

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[ERROR] DATABASE_URL not found in environment")
        return False

    print(f"[INFO] Connecting to database...")

    try:
        engine = create_engine(database_url)

        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[OK] Database connection successful")

        # Create all tables
        print("[INFO] Creating tables...")
        Base.metadata.create_all(bind=engine)
        print("[OK] All tables created successfully")

        # Check which tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"[INFO] Created tables: {', '.join(tables)}")

        # Create some default plans if they don't exist
        create_default_plans(engine)

        return True

    except Exception as e:
        print(f"[ERROR] Failed to create tables: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_default_plans(engine):
    """Create default subscription plans."""
    from sqlalchemy.orm import sessionmaker

    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        # Check if plans already exist
        existing_plans = session.query(Plan).count()
        if existing_plans > 0:
            print(f"[INFO] {existing_plans} plans already exist")
            session.close()
            return

        # Create default plans
        plans = [
            Plan(
                name="Free",
                description="Free tier with basic features",
                price=0,
                currency="INR",
                billing_period="monthly",
                features=["10 code executions per month", "Basic language support"],
                monthly_executions=10,
                max_execution_time=30,
                is_active=True
            ),
            Plan(
                name="Pro",
                description="Professional tier with enhanced features",
                price=29900,  # $299 in cents
                currency="INR",
                billing_period="monthly",
                features=["100 code executions per month", "All language support", "Priority support"],
                monthly_executions=100,
                max_execution_time=60,
                is_active=True
            )
        ]

        for plan in plans:
            session.add(plan)

        session.commit()
        print(f"[OK] Created {len(plans)} default plans")
        session.close()

    except Exception as e:
        print(f"[ERROR] Failed to create default plans: {e}")

if __name__ == "__main__":
    success = create_tables()
    print(f"\n{'='*50}")
    if success:
        print("[SUCCESS] Database setup complete!")
    else:
        print("[ERROR] Database setup failed")

    sys.exit(0 if success else 1)
