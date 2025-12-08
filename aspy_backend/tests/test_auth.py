import requests
from jose import jwt, JWTError
import os
from datetime import datetime


def debug_authentication():
    print("🔍 Debugging Authentication Issues")
    print("=" * 60)

    BASE_URL = "http://localhost:8000"

    # 1. Create test user
    timestamp = int(datetime.now().timestamp())
    user_data = {
        "username": f"debug_user_{timestamp}",
        "email": f"debug_{timestamp}@test.com",
        "password": "DebugPass123!"
    }

    print("\n1. Registering user...")
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=user_data)
    print(f"   Status: {response.status_code}")

    if response.status_code != 201:
        print(f"   Registration failed: {response.text}")
        return

    print("   ✅ User created")

    # 2. Login
    print("\n2. Logging in...")
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"]
    })

    if response.status_code != 200:
        print(f"   Login failed: {response.text}")
        return

    token_data = response.json()
    token = token_data["access_token"]
    print(f"   ✅ Login successful")
    print(f"   Token: {token[:50]}...")

    # 3. Decode token to see contents (using jose library)
    print("\n3. Decoding token...")
    try:
        # Decode without verification to see payload
        decoded = jwt.decode(token, options={"verify_signature": False})
        print(f"   Token payload:")
        print(f"     sub (email): {decoded.get('sub')}")
        print(f"     exp: {decoded.get('exp')}")
        if decoded.get('exp'):
            exp_time = datetime.fromtimestamp(decoded.get('exp'))
            print(f"       ({exp_time})")
        print(f"     iat: {decoded.get('iat')}")
    except Exception as e:
        print(f"   ❌ Cannot decode token: {e}")

    # 4. Test each protected endpoint
    print("\n4. Testing protected endpoints...")

    endpoints = [
        ("/api/v1/auth/me", "GET"),
        ("/api/v1/subscriptions", "GET"),
        ("/api/v1/payments/history", "GET"),
        ("/api/v1/billing/invoices", "GET"),
        ("/api/v1/billing/usage", "GET"),
    ]

    headers = {"Authorization": f"Bearer {token}"}

    for endpoint, method in endpoints:
        print(f"\n   Testing {endpoint}...")
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)

            print(f"     Status: {response.status_code}")

            if response.status_code == 200:
                print(f"     ✅ Success")
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"     Data: {len(data)} items")
                    else:
                        print(f"     Data: {type(data).__name__}")
                except:
                    print(f"     Data: Could not parse JSON")
            elif response.status_code == 401:
                print(f"     ❌ Unauthorized: {response.text}")
            elif response.status_code == 404:
                print(f"     ⚠️ Not found (might be normal): {response.text}")
            else:
                print(f"     ❌ Error: {response.text[:200]}")

        except Exception as e:
            print(f"     ❌ Request failed: {e}")

    # 5. Test token verification with SECRET_KEY
    print("\n5. Testing token verification...")
    secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")

    try:
        # Try to verify the token with jose library
        verified = jwt.decode(token, secret_key, algorithms=["HS256"])
        print(f"   ✅ Token verified successfully with SECRET_KEY")
        print(f"   Email in token: {verified.get('sub')}")
    except JWTError as e:
        print(f"   ❌ Token verification failed: {e}")
        print(f"   SECRET_KEY used: {secret_key[:20]}...")

    print("\n" + "=" * 60)
    print("Debug complete!")


if __name__ == "__main__":
    debug_authentication()