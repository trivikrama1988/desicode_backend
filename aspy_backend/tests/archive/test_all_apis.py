# test_fixed.py - USE THIS INSTEAD
import requests
import json
import time

BASE_URL = "http://localhost:8000"


def test_endpoint(method, endpoint, data=None, token=None, show_response=True):
    """Test an API endpoint"""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{BASE_URL}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            headers["Content-Type"] = "application/json"
            response = requests.post(url, json=data, headers=headers)

        status = "✅" if response.status_code < 400 else "❌"
        print(f"{status} {method} {endpoint} - Status: {response.status_code}")

        if show_response and response.status_code < 500:
            try:
                if response.text:
                    result = response.json()
                    print(f"   Response: {json.dumps(result, indent=2)}")
                    return result
                else:
                    print(f"   Response: (Empty)")
            except:
                print(f"   Response: {response.text[:200]}")

        return None
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None


print("🚀 Testing DesiCodes Backend - FIXED VERSION")
print("=" * 60)

# 1. Root endpoint
print("\n1. Root endpoint:")
test_endpoint("GET", "/")

# 2. Register user
print("\n2. Register user:")
register_data = {
    "username": "test_" + str(int(time.time())),
    "email": f"test{int(time.time())}@test.com",
    "password": "test123"
}
result = test_endpoint("POST", "/api/auth/register", register_data)
token = result.get("access_token") if result else None

if not token:
    print("\n3. Login with demo user:")
    login_data = {
        "email": "demo@desicodes.com",
        "password": "demo123"
    }
    result = test_endpoint("POST", "/api/auth/login", login_data)
    token = result.get("access_token") if result else None

if token:
    print(f"\n✅ Token: {token[:30]}...")

    # 4. Get user profile
    print("\n4. Get user profile:")
    test_endpoint("GET", "/api/auth/me", token=token)

    # 5. Get plans (SHOULD WORK - public endpoint)
    print("\n5. Get subscription plans (public):")
    test_endpoint("GET", "/api/subscriptions/plans")

    # 6. Check subscriptions
    print("\n6. Get user subscriptions:")
    test_endpoint("GET", "/api/subscriptions", token=token)

    # 7. Run code using LEGACY endpoint
    print("\n7. Run Assamese code (query params):")
    # Using query parameters instead of JSON body
    code = "প্ৰিন্ট(\"স্বাগতম!\")"
    encoded_code = requests.utils.quote(code)
    url = f"/api/transpiler/run?code={encoded_code}&language=assamese&timeout=5"
    test_endpoint("POST", url, token=token)

    # 8. Check quota
    print("\n8. Check execution quota:")
    test_endpoint("GET", "/api/transpiler/run/quota", token=token)

    # 9. Get supported languages
    print("\n9. Get supported languages (public):")
    test_endpoint("GET", "/api/transpiler/run/supported-languages")

    # 10. Try new transpiler endpoint
    print("\n10. Try new transpiler endpoint (JSON body):")
    code_data = {
        "code": "প্রিন্ট(\"বাংলা\")",
        "language": "bengali",
        "sync": True
    }
    test_endpoint("POST", "/api/transpiler/", code_data, token=token)

    # 11. Get billing info
    print("\n11. Get billing usage:")
    test_endpoint("GET", "/api/billing/usage", token=token)

    # 12. Get invoices
    print("\n12. Get invoices:")
    test_endpoint("GET", "/api/invoices/my", token=token)

print("\n" + "=" * 60)
print("✅ Testing complete!")
print("Check http://localhost:8000/docs for all available endpoints")
