import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import pwd_context, hash_password


def migrate_user_passwords():
    db = SessionLocal()

    try:
        users = db.query(User).all()
        print(f"Found {len(users)} users")

        for user in users:
            print(f"\nUser: {user.email}")
            print(f"Current hash: {user.password[:50]}...")

            # Check if it's a bcrypt hash (starts with $2b$)
            if user.password.startswith("$2b$"):
                print("  ❌ Password uses bcrypt (will fail with new system)")
                # You need to reset password or keep bcrypt verification
            else:
                print("  ✅ Password hash looks compatible")

        print("\n⚠️ If users have bcrypt hashes, they need to reset passwords")

    finally:
        db.close()


if __name__ == "__main__":
    migrate_user_passwords()