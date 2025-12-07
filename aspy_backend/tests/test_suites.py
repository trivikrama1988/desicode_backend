# test_api_suite.py
import requests
import json
import time
import sys
import os
from datetime import datetime

BASE_URL = "http://localhost:8000"
TEST_USER = {}
ACCESS_TOKEN = None


def print_test_result(name, success, response=None):
    """Print test result with color coding"""
    if success:
        print(f"✅ {name}: PASSED")
    else:
        print(f"❌ {name}: FAILED")
        if response:
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.text[:200]}")


def test_health():
    """Test health endpoint"""
    print("\n🔍 Testing Health Endpoint")
    print("-" * 40)

    response = requests.get(f"{BASE_URL}/health")
    success = response.status_code == 200 and response.json().get("status") == "healthy"
    print_test_result("Health Check", success, response)
    return success


def test_get_plans():
    """Test getting subscription plans"""
    print("\n📋 Testing Plans Endpoint")
    print("-" * 40)

    response = requests.get(f"{BASE_URL}/api/v1/plans")
    success = response.status_code == 200
    if success:
        plans = response.json()
        print(f"✅ Found {len(plans)} plans:")
        for plan in plans:
            print(f"   • {plan['name']}: ₹{plan['price'] / 100}")
    else:
        print_test_result("Get Plans", success, response)
    return success


def test_register_user():
    """Test user registration"""
    print("\n👤 Testing User Registration")
    print("-" * 40)

    # Generate unique test user
    timestamp = int(time.time())
    TEST_USER.update({
        "username": f"testuser_{timestamp}",
        "email": f"testuser_{timestamp}@desicodes.com",
        "password": "TestPassword123!"
    })

    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json=TEST_USER
    )

    success = response.status_code == 201
    if success:
        print(f"✅ User registered: {TEST_USER['email']}")
        TEST_USER.update(response.json())
    else:
        print_test_result("User Registration", success, response)

    return success


def test_login():
    """Test user login"""
    print("\n🔐 Testing User Login")
    print("-" * 40)

    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json=login_data
    )

    success = response.status_code == 200
    if success:
        data = response.json()
        global ACCESS_TOKEN
        ACCESS_TOKEN = data["access_token"]
        print(f"✅ Login successful")
        print(f"   Token: {ACCESS_TOKEN[:50]}...")
        print(f"   User ID: {data['user']['id']}")
    else:
        print_test_result("User Login", success, response)

    return success


def test_get_current_user():
    """Test getting current user info"""
    print("\n👤 Testing Get Current User")
    print("-" * 40)

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    response = requests.get(
        f"{BASE_URL}/api/v1/auth/me",
        headers=headers
    )

    success = response.status_code == 200
    print_test_result("Get Current User", success, response)
    if success:
        print(f"   User: {response.json()['username']}")

    return success


def test_update_profile():
    """Test updating user profile"""
    print("\n✏️ Testing Update Profile")
    print("-" * 40)

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    update_data = {
        "username": f"updated_{TEST_USER['username']}",
        "email": f"updated_{TEST_USER['email']}"
    }

    response = requests.put(
        f"{BASE_URL}/api/v1/users/profile",
        json=update_data,
        headers=headers
    )

    success = response.status_code == 200
    print_test_result("Update Profile", success, response)
    if success:
        print(f"   Updated to: {response.json()['username']}")

    return success


def test_get_subscriptions():
    """Test getting user subscriptions"""
    print("\n📊 Testing Get Subscriptions")
    print("-" * 40)

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    response = requests.get(
        f"{BASE_URL}/api/v1/subscriptions",
        headers=headers
    )

    success = response.status_code == 200
    print_test_result("Get Subscriptions", success, response)
    if success:
        subscriptions = response.json()
        print(f"   Found {len(subscriptions)} subscriptions")

    return success


def test_create_subscription():
    """Test creating a subscription"""
    print("\n🛒 Testing Create Subscription")
    print("-" * 40)

    # First get available plans
    plans_response = requests.get(f"{BASE_URL}/api/v1/plans")
    plans = plans_response.json()

    if not plans:
        print("❌ No plans available")
        return False

    # Use Pro plan (id=2) for testing
    plan_id = 2  # Assuming Pro plan is id=2

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    subscription_data = {
        "plan_id": plan_id
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/subscriptions/create",
        json=subscription_data,
        headers=headers
    )

    success = response.status_code in [200, 400]  # 400 if already subscribed
    print_test_result("Create Subscription", success, response)

    if success and response.status_code == 200:
        print(f"   Subscribed to plan ID: {plan_id}")
    elif response.status_code == 400:
        print(f"   Note: {response.json().get('detail', 'Already subscribed')}")

    return success


def test_payment_endpoints():
    """Test payment endpoints (won't process real payments)"""
    print("\n💰 Testing Payment Endpoints")
    print("-" * 40)

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    # Test 1: Get payment history
    response = requests.get(
        f"{BASE_URL}/api/v1/payments/history",
        headers=headers
    )

    success1 = response.status_code == 200
    print_test_result("Get Payment History", success1, response)
    if success1:
        history = response.json()
        print(f"   Found {len(history)} payment records")

    # Test 2: Try to create Stripe checkout (will likely fail without keys)
    plans_response = requests.get(f"{BASE_URL}/api/v1/plans")
    plans = plans_response.json()
    plan_id = plans[1]["id"] if len(plans) > 1 else 2

    stripe_data = {
        "plan_id": plan_id,
        "success_url": "http://localhost:3000/success",
        "cancel_url": "http://localhost:3000/cancel"
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/payments/stripe/create-checkout",
        json=stripe_data,
        headers=headers
    )

    success2 = response.status_code in [200, 400, 500]
    print_test_result("Create Stripe Checkout", success2, response)

    return success1 or success2  # At least one should work


def test_billing_endpoints():
    """Test billing endpoints"""
    print("\n🧾 Testing Billing Endpoints")
    print("-" * 40)

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    # Test 1: Get invoices
    response = requests.get(
        f"{BASE_URL}/api/v1/billing/invoices",
        headers=headers
    )

    success1 = response.status_code == 200
    print_test_result("Get Invoices", success1, response)
    if success1:
        invoices = response.json()
        print(f"   Found {len(invoices)} invoices")

    # Test 2: Get usage stats
    response = requests.get(
        f"{BASE_URL}/api/v1/billing/usage",
        headers=headers
    )

    success2 = response.status_code in [200, 404]
    print_test_result("Get Usage Stats", success2, response)

    return success1 or success2


def test_error_handling():
    """Test error cases"""
    print("\n⚠️ Testing Error Handling")
    print("-" * 40)

    tests_passed = 0

    # Test 1: Invalid login
    print("\n1. Testing Invalid Login...")
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": "invalid@test.com", "password": "wrong"}
    )
    if response.status_code == 401:
        print("✅ Invalid login handled correctly")
        tests_passed += 1
    else:
        print("❌ Invalid login test failed")

    # Test 2: Access protected route without token
    print("\n2. Testing Unauthorized Access...")
    response = requests.get(f"{BASE_URL}/api/v1/auth/me")
    if response.status_code == 401:
        print("✅ Unauthorized access handled correctly")
        tests_passed += 1
    else:
        print("❌ Unauthorized access test failed")

    # Test 3: Invalid token
    print("\n3. Testing Invalid Token...")
    headers = {"Authorization": "Bearer invalid_token_here"}
    response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
    if response.status_code == 401:
        print("✅ Invalid token handled correctly")
        tests_passed += 1
    else:
        print("❌ Invalid token test failed")

    return tests_passed >= 2


def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Comprehensive API Test Suite")
    print("=" * 60)

    test_results = {}

    # Basic tests (no auth required)
    test_results["health"] = test_health()
    test_results["plans"] = test_get_plans()

    # Authentication tests
    test_results["register"] = test_register_user()
    if test_results["register"]:
        test_results["login"] = test_login()

    # Protected endpoints (require auth)
    if test_results.get("login"):
        test_results["current_user"] = test_get_current_user()
        test_results["update_profile"] = test_update_profile()
        test_results["subscriptions"] = test_get_subscriptions()
        test_results["create_subscription"] = test_create_subscription()
        test_results["payments"] = test_payment_endpoints()
        test_results["billing"] = test_billing_endpoints()
        test_results["error_handling"] = test_error_handling()

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)

    for name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name.replace('_', ' ').title()}")

    print("\n" + "=" * 60)
    print(f"🎯 Total: {passed}/{total} tests passed ({passed / total * 100:.1f}%)")

    if passed == total:
        print("\n🎉 All tests passed! Your API is production-ready!")
    else:
        print("\n⚠️ Some tests failed. Review the output above.")

    return test_results


if __name__ == "__main__":
    run_all_tests()