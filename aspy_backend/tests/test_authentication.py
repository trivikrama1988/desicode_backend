import requests
import time
import jwt  # For decoding token

BASE_URL = "http://localhost:8000"


def debug_authentication():
    print("🔍 Debugging Authentication Issues")
    print("=" * 60)

    # Step 1: Create test user
    timestamp = int(time.time())
    user_data = {
        "username": f"debug_user_{timestamp}",
        "email": f"debug_{timestamp}@test.com",
        "password": "DebugPass123!"
    }

    print("\n1. Registering user...")
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=user_data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}")

    if response.status_code == 201:
        user = response.json()
        print(f"   ✅ User created: ID={user['id']}")

    # Step 2: Login
    print("\n2. Logging in...")
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }

    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}")

    if response.status_code == 200:
        token_data = response.json()
        token = token_data.get("access_token")
        print(f"   ✅ Token received: {token[:50]}...")

        # Decode token to inspect
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            print(f"   Token payload: {decoded}")
        except:
            print("   ❌ Cannot decode token")

        # Step 3: Test /auth/me endpoint
        print("\n3. Testing /auth/me...")
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")

        if response.status_code == 200:
            print("   ✅ Authentication successful!")

            # Step 4: Test other endpoints
            endpoints = [
                ("/api/v1/subscriptions", "GET"),
                ("/api/v1/payments/history", "GET"),
                ("/api/v1/billing/invoices", "GET"),
            ]

            for endpoint, method in endpoints:
                print(f"\n4. Testing {endpoint}...")
                response = requests.request(method, f"{BASE_URL}{endpoint}", headers=headers)
                print(f"   Status: {response.status_code}")
                if response.status_code != 200:
                    print(f"   Response: {response.text[:200]}")

        else:
            # Check headers
            print(f"   Response headers: {dict(response.headers)}")

    else:
        # Check if it's a password hash issue
        print("\⚠️ Login failed. Checking password hash...")

        # Get the user from database to check hash
        from app.db.session import SessionLocal
        from app.models.user import User
        from app.core.security import verify_password

        db = SessionLocal()
        user = db.query(User).filter(User.email == user_data["email"]).first()
        if user:
            print(f"   User found in DB: {user.email}")
            print(f"   Hashed password in DB: {user.password[:50]}...")

            # Test password verification
            is_correct = verify_password(user_data["password"], user.password)
            print(f"   Password verification: {is_correct}")
        db.close()


if __name__ == "__main__":
    debug_authentication()
