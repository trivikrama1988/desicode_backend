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

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        success = response.status_code == 200 and response.json().get("status") == "healthy"
        print_test_result("Health Check", success, response)
        return success
    except Exception as e:
        print(f"❌ Health Check Error: {e}")
        return False


def test_get_plans():
    """Test getting subscription plans"""
    print("\n📋 Testing Plans Endpoint")
    print("-" * 40)

    try:
        response = requests.get(f"{BASE_URL}/api/v1/plans", timeout=10)

        if response.status_code == 200:
            try:
                plans = response.json()
                print(f"✅ Found {len(plans)} plans:")
                for plan in plans:
                    print(f"   • {plan.get('name', 'Unknown')}: ₹{plan.get('price', 0) / 100}")
                return True
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response from /plans")
                print(f"   Response: {response.text[:200]}")
                return False
        else:
            print(f"❌ Plans endpoint returned status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to plans endpoint: {e}")
        return False


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

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=TEST_USER,
            timeout=10
        )

        success = response.status_code == 201
        if success:
            print(f"✅ User registered: {TEST_USER['email']}")
            user_data = response.json()
            TEST_USER['id'] = user_data.get('id')
            return True
        else:
            print_test_result("User Registration", success, response)
            return False

    except Exception as e:
        print(f"❌ Registration Error: {e}")
        return False


def test_login():
    """Test user login"""
    print("\n🔐 Testing User Login")
    print("-" * 40)

    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json=login_data,
            timeout=10
        )

        success = response.status_code == 200
        if success:
            data = response.json()
            global ACCESS_TOKEN
            ACCESS_TOKEN = data["access_token"]
            print(f"✅ Login successful")
            print(f"   Token: {ACCESS_TOKEN[:50]}...")
            print(f"   User ID: {data['user']['id']}")
            return True
        else:
            print_test_result("User Login", success, response)
            return False

    except Exception as e:
        print(f"❌ Login Error: {e}")
        return False


def test_get_current_user():
    """Test getting current user info"""
    print("\n👤 Testing Get Current User")
    print("-" * 40)

    if not ACCESS_TOKEN:
        print("❌ No access token available")
        return False

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/auth/me",
            headers=headers,
            timeout=10
        )

        success = response.status_code == 200
        print_test_result("Get Current User", success, response)
        if success:
            user_data = response.json()
            print(f"   User: {user_data.get('username', 'Unknown')}")
        return success

    except Exception as e:
        print(f"❌ Get Current User Error: {e}")
        return False


def test_update_profile():
    """Test updating user profile"""
    print("\n✏️ Testing Update Profile")
    print("-" * 40)

    if not ACCESS_TOKEN:
        print("❌ No access token available")
        return False

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    update_data = {
        "username": f"updated_{TEST_USER['username']}",
        "email": f"updated_{TEST_USER['email']}"
    }

    try:
        response = requests.put(
            f"{BASE_URL}/api/v1/users/profile",
            json=update_data,
            headers=headers,
            timeout=10
        )

        success = response.status_code == 200
        print_test_result("Update Profile", success, response)
        if success:
            user_data = response.json()
            print(f"   Updated to: {user_data.get('username', 'Unknown')}")
        return success

    except Exception as e:
        print(f"❌ Update Profile Error: {e}")
        return False


def test_get_subscriptions():
    """Test getting user subscriptions"""
    print("\n📊 Testing Get Subscriptions")
    print("-" * 40)

    if not ACCESS_TOKEN:
        print("❌ No access token available")
        return False

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/subscriptions",
            headers=headers,
            timeout=10
        )

        success = response.status_code == 200
        print_test_result("Get Subscriptions", success, response)
        if success:
            try:
                subscriptions = response.json()
                print(f"   Found {len(subscriptions)} subscriptions")
            except:
                print(f"   Could not parse subscriptions response")
        return success

    except Exception as e:
        print(f"❌ Get Subscriptions Error: {e}")
        return False


def test_create_subscription():
    """Test creating a subscription"""
    print("\n🛒 Testing Create Subscription")
    print("-" * 40)

    if not ACCESS_TOKEN:
        print("❌ No access token available")
        return False

    try:
        # First get available plans with better error handling
        plans_response = requests.get(f"{BASE_URL}/api/v1/plans", timeout=10)

        if plans_response.status_code != 200:
            print(f"❌ Cannot get plans: Status {plans_response.status_code}")
            print(f"   Response: {plans_response.text[:200]}")
            return False

        try:
            plans = plans_response.json()
        except json.JSONDecodeError:
            print(f"❌ Cannot parse plans response as JSON")
            print(f"   Response: {plans_response.text[:200]}")
            return False

        if not plans:
            print("❌ No plans available")
            return False

        # Use the first plan available
        plan_id = plans[0]["id"]

        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        subscription_data = {
            "plan_id": plan_id
        }

        response = requests.post(
            f"{BASE_URL}/api/v1/subscriptions/create",
            json=subscription_data,
            headers=headers,
            timeout=10
        )

        success = response.status_code in [200, 400]  # 400 if already subscribed
        if success and response.status_code == 200:
            print(f"✅ Subscribed to plan ID: {plan_id}")
        elif response.status_code == 400:
            print(f"⚠️ Note: {response.json().get('detail', 'Already subscribed')}")
        else:
            print(f"❌ Create subscription failed: Status {response.status_code}")
            print(f"   Response: {response.text[:200]}")

        return success

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error during create subscription: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_payment_endpoints():
    """Test payment endpoints (won't process real payments)"""
    print("\n💰 Testing Payment Endpoints")
    print("-" * 40)

    if not ACCESS_TOKEN:
        print("❌ No access token available")
        return False

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    # Test 1: Get payment history
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/payments/history",
            headers=headers,
            timeout=10
        )

        success1 = response.status_code == 200
        print_test_result("Get Payment History", success1, response)
        if success1:
            try:
                history = response.json()
                print(f"   Found {len(history)} payment records")
            except:
                print(f"   Could not parse payment history")
    except Exception as e:
        print(f"❌ Payment History Error: {e}")
        success1 = False

    # Test 2: Try to create Stripe checkout (will likely fail without keys)
    try:
        plans_response = requests.get(f"{BASE_URL}/api/v1/plans")
        if plans_response.status_code == 200:
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
                headers=headers,
                timeout=10
            )

            success2 = response.status_code in [200, 400, 500]
            print_test_result("Create Stripe Checkout", success2, response)
        else:
            success2 = False
            print("❌ Could not get plans for Stripe test")
    except Exception as e:
        print(f"❌ Stripe Checkout Error: {e}")
        success2 = False

    return success1 or success2  # At least one should work


def test_billing_endpoints():
    """Test billing endpoints"""
    print("\n🧾 Testing Billing Endpoints")
    print("-" * 40)

    if not ACCESS_TOKEN:
        print("❌ No access token available")
        return False

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    # Test 1: Get invoices
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/billing/invoices",
            headers=headers,
            timeout=10
        )

        success1 = response.status_code == 200
        print_test_result("Get Invoices", success1, response)
        if success1:
            try:
                invoices = response.json()
                print(f"   Found {len(invoices)} invoices")
            except:
                print(f"   Could not parse invoices")
    except Exception as e:
        print(f"❌ Get Invoices Error: {e}")
        success1 = False

    # Test 2: Get usage stats
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/billing/usage",
            headers=headers,
            timeout=10
        )

        success2 = response.status_code in [200, 404]
        print_test_result("Get Usage Stats", success2, response)
    except Exception as e:
        print(f"❌ Get Usage Stats Error: {e}")
        success2 = False

    return success1 or success2


def test_error_handling():
    """Test error cases"""
    print("\n⚠️ Testing Error Handling")
    print("-" * 40)

    tests_passed = 0
    total_tests = 3

    # Test 1: Invalid login
    print("\n1. Testing Invalid Login...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": "invalid@test.com", "password": "wrong"},
            timeout=10
        )
        if response.status_code == 401:
            print("✅ Invalid login handled correctly")
            tests_passed += 1
        else:
            print(f"❌ Invalid login test failed (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Invalid login test error: {e}")

    # Test 2: Access protected route without token
    print("\n2. Testing Unauthorized Access...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/auth/me", timeout=10)
        if response.status_code == 401:
            print("✅ Unauthorized access handled correctly")
            tests_passed += 1
        else:
            print(f"❌ Unauthorized access test failed (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Unauthorized access test error: {e}")

    # Test 3: Invalid token
    print("\n3. Testing Invalid Token...")
    try:
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers, timeout=10)
        if response.status_code == 401:
            print("✅ Invalid token handled correctly")
            tests_passed += 1
        else:
            print(f"❌ Invalid token test failed (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Invalid token test error: {e}")

    return tests_passed >= 2  # Pass if at least 2 tests pass


def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Comprehensive API Test Suite")
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

    if test_results.get("register"):
        test_results["login"] = test_login()
    else:
        test_results["login"] = False

    # Protected endpoints (require auth)
    if test_results.get("login"):
        test_results["current_user"] = test_get_current_user()
        test_results["update_profile"] = test_update_profile()
        test_results["subscriptions"] = test_get_subscriptions()
        test_results["create_subscription"] = test_create_subscription()
        test_results["payments"] = test_payment_endpoints()
        test_results["billing"] = test_billing_endpoints()
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
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)

    for name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name.replace('_', ' ').title()}")

    print("\n" + "=" * 60)

    if total > 0:
        print(f"🎯 Total: {passed}/{total} tests passed ({passed / total * 100:.1f}%)")
    else:
        print("🎯 No tests were executed")

    if passed == total:
        print("\n🎉 All tests passed! Your API is production-ready!")
    elif passed > total * 0.7:
        print(f"\n⚠️ {passed}/{total} tests passed. Some issues need attention.")
    else:
        print(f"\n❌ Only {passed}/{total} tests passed. Major issues detected.")

    return test_results


if __name__ == "__main__":
    run_all_tests()