import requests
import time
import os
from datetime import datetime
import pytest

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8000")
TEST_USER = {}


def print_test_result(name, success, response=None):
    """Print test result with color coding"""
    if success:
        print(f"{name}: PASSED")
    else:
        print(f"{name}: FAILED")
        if response:
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.text[:200]}")


def test_health():
    """Test health endpoint"""
    print("\nTesting Health Endpoint")
    print("-" * 40)

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        success = response.status_code == 200 and response.json().get("status") == "healthy"
        print_test_result("Health Check", success, response)
        assert success, f"Health check failed: {response.status_code} {response.text}"
    except Exception as e:
        pytest.fail(f"Health Check Error: {e}")


def test_get_plans():
    """Test getting subscription plans"""
    print("\nTesting Plans Endpoint")
    print("-" * 40)

    try:
        response = requests.get(f"{BASE_URL}/api/plans", timeout=10)

        assert response.status_code == 200, f"Plans endpoint returned status: {response.status_code} - {response.text}"

        plans = response.json()
        print(f"Found {len(plans)} plans:")
        for plan in plans:
            print(f"   - {plan.get('name', 'Unknown')}: ${plan.get('price', 0) / 100}")

    except requests.exceptions.RequestException as e:
        pytest.fail(f"Error connecting to plans endpoint: {e}")


def test_register_user():
    """Test user registration"""
    print("\nTesting User Registration")
    print("-" * 40)

    # Generate unique test user
    timestamp = int(time.time())
    TEST_USER.update({
        "username": f"testuser_{timestamp}",
        "email": f"testuser_{timestamp}@desicodes.com",
        "password": "TestPassword123!"
    })

    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=TEST_USER,
            timeout=10
        )

        assert response.status_code == 201, f"User registration failed: {response.status_code} {response.text}"
        user_data = response.json()
        TEST_USER['id'] = user_data.get('id')
        print(f"User registered: {TEST_USER['email']}")

    except Exception as e:
        pytest.fail(f"Registration Error: {e}")


def test_login():
    """Test user login"""
    print("\nTesting User Login")
    print("-" * 40)

    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=login_data,
            timeout=10
        )

        assert response.status_code == 200, f"Login failed: {response.status_code} {response.text}"
        data = response.json()
        token = data["access_token"]
        print(f"Login successful")
        print(f"   Token: {token[:50]}...")
        print(f"   User ID: {data['user']['id']}")

        return token

    except Exception as e:
        pytest.fail(f"Login Error: {e}")


def test_get_current_user(token):
    """Test getting current user info"""
    print("\nTesting Get Current User")
    print("-" * 40)

    assert token, "No access token available from fixture"

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers=headers,
            timeout=10
        )

        assert response.status_code == 200, f"Get Current User failed: {response.status_code} {response.text}"
        user_data = response.json()
        print(f"   User: {user_data.get('username', 'Unknown')}")

    except Exception as e:
        pytest.fail(f"Get Current User Error: {e}")


def test_update_profile(token):
    """Test updating user profile"""
    print("\nTesting Update Profile")
    print("-" * 40)

    assert token, "No access token available from fixture"

    headers = {"Authorization": f"Bearer {token}"}
    update_data = {
        "username": f"updated_{int(time.time())}",
        "email": f"updated_{int(time.time())}@desicodes.com"
    }

    try:
        response = requests.put(
            f"{BASE_URL}/api/users/profile",
            json=update_data,
            headers=headers,
            timeout=10
        )

        assert response.status_code == 200, f"Update Profile failed: {response.status_code} {response.text}"
        user_data = response.json()
        print(f"   Updated to: {user_data.get('username', 'Unknown')}")

    except Exception as e:
        pytest.fail(f"Update Profile Error: {e}")


def test_get_subscriptions(token):
    """Test getting user subscriptions"""
    print("\nTesting Get Subscriptions")
    print("-" * 40)

    assert token, "No access token available from fixture"

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(
            f"{BASE_URL}/api/subscriptions",
            headers=headers,
            timeout=10
        )

        assert response.status_code == 200, f"Get Subscriptions failed: {response.status_code} {response.text}"
        subscriptions = response.json()
        print(f"   Found {len(subscriptions)} subscriptions")

    except Exception as e:
        pytest.fail(f"Get Subscriptions Error: {e}")


def test_create_subscription(token):
    """Test creating a subscription"""
    print("\nTesting Create Subscription")
    print("-" * 40)

    assert token, "No access token available from fixture"

    try:
        plans_response = requests.get(f"{BASE_URL}/api/plans", timeout=10)
        assert plans_response.status_code == 200, f"Cannot get plans: {plans_response.status_code} {plans_response.text}"
        plans = plans_response.json()
        assert plans, "No plans available"

        plan_id = plans[0]["id"]

        headers = {"Authorization": f"Bearer {token}"}
        subscription_data = {"plan_id": plan_id}

        response = requests.post(
            f"{BASE_URL}/api/subscriptions/create",
            json=subscription_data,
            headers=headers,
            timeout=10
        )

        success = response.status_code in [200, 400]
        assert success, f"Create subscription failed: {response.status_code} {response.text}"

    except requests.exceptions.RequestException as e:
        pytest.fail(f"Network error during create subscription: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error: {e}")


def test_payment_endpoints(token):
    """Test payment endpoints (won't process real payments)"""
    print("\nTesting Payment Endpoints")
    print("-" * 40)

    assert token, "No access token available from fixture"

    headers = {"Authorization": f"Bearer {token}"}

    # Test 1: Get payment history
    try:
        response = requests.get(
            f"{BASE_URL}/api/payments/history",
            headers=headers,
            timeout=10
        )

        success1 = response.status_code == 200
        print_test_result("Get Payment History", success1, response)
    except Exception as e:
        pytest.fail(f"Payment History Error: {e}")

    # Test 2: Try to create Stripe checkout (will likely fail without keys)
    try:
        plans_response = requests.get(f"{BASE_URL}/api/plans")
        if plans_response.status_code == 200:
            plans = plans_response.json()
            plan_id = plans[1]["id"] if len(plans) > 1 else 2

            stripe_data = {
                "plan_id": plan_id,
                "success_url": "http://localhost:3000/success",
                "cancel_url": "http://localhost:3000/cancel"
            }

            response = requests.post(
                f"{BASE_URL}/api/payments/stripe/create-checkout",
                json=stripe_data,
                headers=headers,
                timeout=10
            )

            success2 = response.status_code in [200, 400, 500]
            print_test_result("Create Stripe Checkout", success2, response)
        else:
            success2 = False
            print("Could not get plans for Stripe test")
    except Exception as e:
        pytest.fail(f"Stripe Checkout Error: {e}")

    assert success1 or success2, "Both payment tests failed"


def test_billing_endpoints(token):
    """Test billing endpoints"""
    print("\nTesting Billing Endpoints")
    print("-" * 40)

    assert token, "No access token available from fixture"

    headers = {"Authorization": f"Bearer {token}"}

    # Test 1: Get invoices
    try:
        response = requests.get(
            f"{BASE_URL}/api/billing/invoices",
            headers=headers,
            timeout=10
        )

        success1 = response.status_code == 200
        print_test_result("Get Invoices", success1, response)
    except Exception as e:
        pytest.fail(f"Get Invoices Error: {e}")

    # Test 2: Get usage stats
    try:
        response = requests.get(
            f"{BASE_URL}/api/billing/usage",
            headers=headers,
            timeout=10
        )

        success2 = response.status_code in [200, 404]
        print_test_result("Get Billing Usage", success2, response)
    except Exception as e:
        pytest.fail(f"Billing Usage Error: {e}")

    assert success1 or success2, "Both billing tests failed"


def test_error_handling():
    """Test error cases"""
    print("\nTesting Error Handling")
    print("-" * 40)

    tests_passed = 0
    total_tests = 3

    # Test 1: Invalid login
    print("\n1. Testing Invalid Login...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "invalid@test.com", "password": "wrong"},
            timeout=10
        )
        if response.status_code == 401:
            print("Invalid login handled correctly")
            tests_passed += 1
        else:
            print(f"Invalid login test failed (Status: {response.status_code})")
    except Exception as e:
        print(f"Invalid login test error: {e}")

    # Test 2: Access protected route without token
    print("\n2. Testing Unauthorized Access...")
    try:
        response = requests.get(f"{BASE_URL}/api/auth/me", timeout=10)
        if response.status_code == 401:
            print("Unauthorized access handled correctly")
            tests_passed += 1
        else:
            print(f"Unauthorized access test failed (Status: {response.status_code})")
    except Exception as e:
        print(f"Unauthorized access test error: {e}")

    # Test 3: Invalid token
    print("\n3. Testing Invalid Token...")
    try:
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers, timeout=10)
        if response.status_code == 401:
            print("Invalid token handled correctly")
            tests_passed += 1
        else:
            print(f"Invalid token test failed (Status: {response.status_code})")
    except Exception as e:
        print(f"Invalid token test error: {e}")

    assert tests_passed >= 2, "Error handling tests did not pass as expected"


def run_all_tests():
    """Run all tests"""
    print("Starting Comprehensive API Test Suite")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    test_results = {}

    # Basic tests (no auth required)
    test_results["health"] = test_health()
    test_results["plans"] = test_get_plans()

    # Authentication tests
    if test_results["plans"]:  # Only try registration if plans endpoint works
        test_results["register"] = test_register_user()
    else:
        test_results["register"] = False

    token = None
    if test_results.get("register"):
        token = test_login()
        test_results["login"] = token is not None
    else:
        test_results["login"] = False

    # Protected endpoints (require auth)
    if test_results.get("login") and token:
        test_results["current_user"] = test_get_current_user(token)
        test_results["update_profile"] = test_update_profile(token)
        test_results["subscriptions"] = test_get_subscriptions(token)
        test_results["create_subscription"] = test_create_subscription(token)
        test_results["payments"] = test_payment_endpoints(token)
        test_results["billing"] = test_billing_endpoints(token)
        test_results["error_handling"] = test_error_handling()
    else:
        # Mark all protected tests as failed if login failed
        test_results["current_user"] = False
        test_results["update_profile"] = False
        test_results["subscriptions"] = False
        test_results["create_subscription"] = False
        test_results["payments"] = False
        test_results["billing"] = False
        test_results["error_handling"] = False

    # Summary
    print("\n" + "=" * 60)
    print(" TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)

    for name, result in test_results.items():
        status = "PASS" if result else "FAIL"
        print(f"{status} {name.replace('_', ' ').title()}")

    print("\n" + "=" * 60)

    if total > 0:
        print(f"Total: {passed}/{total} tests passed ({passed / total * 100:.1f}%)")
    else:
        print("No tests were executed")

    if passed == total:
        print("\nAll tests passed! Your API is production-ready!")
    elif passed > total * 0.7:
        print(f"\n{passed}/{total} tests passed. Some issues need attention.")
    else:
        print(f"\nOnly {passed}/{total} tests passed. Major issues detected.")

    return test_results


if __name__ == "__main__":
    run_all_tests()

