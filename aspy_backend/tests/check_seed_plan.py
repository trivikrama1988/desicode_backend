import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import SessionLocal
from app.models.subscription import Plan, PlanType


def check_and_seed_plans():
    db = SessionLocal()

    try:
        # Check if plans exist
        plans = db.query(Plan).all()
        print(f"Found {len(plans)} plans in database")

        if len(plans) == 0:
            print("Seeding plans...")

            plans_data = [
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

            for plan_data in plans_data:
                plan = Plan(**plan_data)
                db.add(plan)
                print(f"Added plan: {plan_data['name']}")

            db.commit()
            print("Plans seeded successfully!")
        else:
            print("Plans already exist in database:")
            for plan in plans:
                print(f"  - {plan.name}: ₹{plan.price / 100}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    check_and_seed_plans()