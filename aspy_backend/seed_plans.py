import sys
import os
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import ALL models to ensure they're registered with SQLAlchemy
from app.models.user import User
from app.models.subscription import Plan, PlanType, Subscription
from app.models.invoice import Invoice

# Now import session
from app.db.session import SessionLocal

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
    seed_plans()