import requests


def test_auth_flow():
    BASE_URL = "http://localhost:8000"

    print("🧪 Testing Authentication Flow")
    print("=" * 40)

    # 1. Create new user
    import time
    timestamp = int(time.time())
    user_data = {
        "username": f"fix_test_{timestamp}",
        "email": f"fix_test_{timestamp}@test.com",
        "password": "TestPass123!"
    }

    print("\n1. Registering...")
    r = requests.post(f"{BASE_URL}/api/v1/auth/register", json=user_data)
    print(f"   Status: {r.status_code}")

    if r.status_code == 201:
        print("   ✅ Registration successful")

        # 2. Login
        print("\n2. Logging in...")
        r = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        print(f"   Status: {r.status_code}")

        if r.status_code == 200:
            token = r.json()["access_token"]
            print(f"   ✅ Login successful")
            print(f"   Token: {token[:50]}...")

            # 3. Test protected endpoints
            headers = {"Authorization": f"Bearer {token}"}
            endpoints = [
                "/api/v1/auth/me",
                "/api/v1/subscriptions",
                "/api/v1/payments/history",
                "/api/v1/billing/invoices",
            ]

            print("\n3. Testing protected endpoints...")
            for endpoint in endpoints:
                r = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
                print(f"   {endpoint}: {r.status_code}")

        else:
            print(f"   ❌ Login failed: {r.text}")
    else:
        print(f"   ❌ Registration failed: {r.text}")


if __name__ == "__main__":
    test_auth_flow()

