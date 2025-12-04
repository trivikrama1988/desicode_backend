import requests
import json
import time

BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}


def print_response(label, response):
    print(f"\n{'=' * 60}")
    print(f"{label}")
    print(f"{'=' * 60}")
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")


def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print_response("Ok  Health Check", response)
    return response.status_code == 200


def test_root():
    """Test root endpoint"""
    response = requests.get(f"{BASE_URL}/")
    print_response(" Root Endpoint", response)
    return response.status_code == 200


def test_get_plans():
    """Test getting all subscription plans"""
    response = requests.get(f"{BASE_URL}/api/v1/plans")
    print_response("Report Get All Plans", response)
    return response.status_code == 200


def test_register_user(email, username, password):
    """Test user registration"""
    data = {
        "username": username,
        "email": email,
        "password": password
    }
    response = requests.post(f"{BASE_URL}/api/v1/auth/register",
                             json=data, headers=HEADERS)
    print_response(" Register User", response)
    return response.status_code == 201, response.json() if response.status_code == 201 else None


def test_login(email, password):
    """Test user login"""
    data = {
        "email": email,
        "password": password
    }
    response = requests.post(f"{BASE_URL}/api/v1/auth/login",
                             json=data, headers=HEADERS)
    print_response(" User Login", response)

    if response.status_code == 200:
        data = response.json()
        return True, data.get("access_token"), data.get("user")
    return False, None, None


def test_get_current_user(token):
    """Test getting current user profile with token"""
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
    print_response(" Get Current User", response)
    return response.status_code == 200, response.json() if response.status_code == 200 else None


def test_get_user_profile(token):
    """Test getting user profile"""
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    response = requests.get(f"{BASE_URL}/api/v1/users/profile", headers=headers)
    print_response("📄 Get User Profile", response)
    return response.status_code == 200, response.json() if response.status_code == 200 else None


def test_update_user_profile(token, new_username, new_email):
    """Test updating user profile"""
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    data = {
        "username": new_username,
        "email": new_email
    }
    response = requests.put(f"{BASE_URL}/api/v1/users/profile",
                            json=data, headers=headers)
    print_response("Update User Profile", response)
    return response.status_code == 200, response.json() if response.status_code == 200 else None


def test_get_user_subscriptions(token):
    """Test getting user subscriptions"""
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    response = requests.get(f"{BASE_URL}/api/v1/subscriptions", headers=headers)
    print_response(" Get User Subscriptions", response)
    return response.status_code == 200, response.json() if response.status_code == 200 else None


def test_create_subscription(token, plan_id):
    """Test creating a subscription"""
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    data = {
        "plan_id": plan_id
    }
    response = requests.post(f"{BASE_URL}/api/v1/subscriptions/create",
                             json=data, headers=headers)
    print_response("Cart Create Subscription", response)
    return response.status_code == 200, response.json() if response.status_code == 200 else None


def test_get_invoices(token):
    """Test getting user invoices"""
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    response = requests.get(f"{BASE_URL}/api/v1/billing/invoices", headers=headers)
    print_response("Get User Invoices", response)
    return response.status_code == 200, response.json() if response.status_code == 200 else None


def test_get_payment_history(token):
    """Test getting payment history"""
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    response = requests.get(f"{BASE_URL}/api/v1/payments/history", headers=headers)
    print_response(" Get Payment History", response)
    return response.status_code == 200, response.json() if response.status_code == 200 else None


def test_create_stripe_checkout(token, plan_id):
    """Test creating Stripe checkout session (will fail without Stripe keys)"""
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    data = {
        "plan_id": plan_id,
        "success_url": "http://localhost:3000/success",
        "cancel_url": "http://localhost:3000/cancel"
    }
    response = requests.post(f"{BASE_URL}/api/v1/payments/stripe/create-checkout",
                             json=data, headers=headers)
    print_response("  card Create Stripe Checkout", response)
    return response.status_code == 200, response.json() if response.status_code == 200 else None


def test_get_usage_stats(token):
    """Test getting usage statistics"""
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    response = requests.get(f"{BASE_URL}/api/v1/billing/usage", headers=headers)
    print_response("Stat Get Usage Stats", response)
    return response.status_code == 200, response.json() if response.status_code == 200 else None


def run_all_tests():
    """Run all API tests"""
    print("\n" + "=" * 80)
    print(" STARTING ASPY BACKEND API TESTS")
    print("=" * 80)

    # Test credentials
    test_email = f"testuser_{int(time.time())}@example.com"
    test_username = f"testuser_{int(time.time())}"
    test_password = "TestPassword123!"

    # Track results
    results = {}
    token = None
    user_data = None

    # Step 1: Test basic endpoints
    print("\n BASIC ENDPOINT TESTS")
    results["health"] = test_health()
    results["root"] = test_root()
    results["get_plans"] = test_get_plans()

    # Get a plan ID for testing
    plans_response = requests.get(f"{BASE_URL}/api/v1/plans")
    if plans_response.status_code == 200:
        plans = plans_response.json()
        plan_id = plans[1]["id"] if len(plans) > 1 else 1  # Use Pro plan if available
    else:
        plan_id = 2  # Default to Pro plan

    # Step 2: Test authentication
    print("\n AUTHENTICATION TESTS")
    success, user_response = test_register_user(test_email, test_username, test_password)
    results["register"] = success

    if success:
        success, token, user_data = test_login(test_email, test_password)
        results["login"] = success

    # Only continue if we have a valid token
    if token:
        # Step 3: Test user endpoints
        print("\n USER PROFILE TESTS")
        results["get_current_user"] = test_get_current_user(token)[0]
        results["get_user_profile"] = test_get_user_profile(token)[0]

        # Update profile with slightly different email
        new_email = f"updated_{test_email}"
        results["update_profile"] = test_update_user_profile(token, f"updated_{test_username}", new_email)[0]

        # Step 4: Test subscription endpoints
        print("\nCart SUBSCRIPTION TESTS")
        results["get_subscriptions"] = test_get_user_subscriptions(token)[0]

        # Only create subscription if user doesn't have one
        subscriptions = test_get_user_subscriptions(token)[1]
        if subscriptions and len(subscriptions) > 0:
            print("User already has subscriptions, skipping create subscription test")
            results["create_subscription"] = False
        else:
            results["create_subscription"] = test_create_subscription(token, plan_id)[0]

        # Step 5: Test billing endpoints
        print("\n BILLING TESTS")
        results["get_invoices"] = test_get_invoices(token)[0]
        results["get_payment_history"] = test_get_payment_history(token)[0]

        # Step 6: Test payment endpoints (will likely fail without proper keys)
        print("\n  Card PAYMENT TESTS")
        results["stripe_checkout"] = test_create_stripe_checkout(token, plan_id)[0]

        # Step 7: Test usage stats
        print("\nStat USAGE TESTS")
        results["get_usage_stats"] = test_get_usage_stats(token)[0]

    # Summary
    print("\n" + "=" * 80)
    print("Report TEST SUMMARY")
    print("=" * 80)

    passed = 0
    total = 0

    for test_name, result in results.items():
        total += 1
        if result:
            passed += 1
            print(f"Ok  {test_name}: PASSED")
        else:
            print(f"   {test_name}: FAILED")

    print(f"\n Total: {passed}/{total} tests passed ({passed / total * 100:.1f}%)")

    if token:
        print(f"\n🔑 Test Token: {token[:50]}...")
        print(f" Test User ID: {user_data.get('id') if user_data else 'N/A'}")
        print(f"Test Email: {test_email}")
        print(f" Test Password: {test_password}")

    return passed == total


if __name__ == "__main__":
    print("Make sure the server is running: uvicorn app.main:app --reload")
    print("Press Ctrl+C to stop testing at any time\n")

    try:
        success = run_all_tests()
        if success:
            print("\n   All tests passed!")
        else:
            print("\nSome tests failed. Check the output above for details.")
    except requests.exceptions.ConnectionError:
        print("\n   Cannot connect to server. Make sure it's running on http://localhost:8000")
        print("   Start it with: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n   Unexpected error: {e}")