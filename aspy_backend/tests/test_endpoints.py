import requests
import json
import time
from datetime import datetime


class APITester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.token = None
        self.user_data = None

    def print_result(self, test_name, success, response=None):
        if success:
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
            if response:
                print(f"   Status: {response.status_code}")
                print(f"   Error: {response.text[:200]}")

    def test_health(self):
        print("\n🔍 Testing Health Endpoint")
        print("-" * 40)
        response = requests.get(f"{self.base_url}/health")
        success = response.status_code == 200
        self.print_result("Health Check", success, response)
        return success

    def test_plans(self):
        print("\n📋 Testing Plans Endpoint")
        print("-" * 40)
        response = requests.get(f"{self.base_url}/api/v1/plans")

        if response.status_code == 200:
            plans = response.json()
            print(f"✅ Found {len(plans)} plans:")
            for plan in plans:
                print(f"   • {plan['name']}: ₹{plan['price'] / 100}")
            return True
        else:
            self.print_result("Get Plans", False, response)
            return False

    def create_test_user(self):
        print("\n👤 Creating Test User")
        print("-" * 40)

        timestamp = int(time.time())
        self.user_data = {
            "username": f"testuser_{timestamp}",
            "email": f"testuser_{timestamp}@desicodes.com",
            "password": "TestPassword123!"
        }

        response = requests.post(
            f"{self.base_url}/api/v1/auth/register",
            json=self.user_data
        )

        if response.status_code == 201:
            print(f"✅ User created: {self.user_data['email']}")
            return True
        else:
            self.print_result("User Registration", False, response)
            return False

    def login_user(self):
        print("\n🔐 Testing User Login")
        print("-" * 40)

        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={
                "email": self.user_data["email"],
                "password": self.user_data["password"]
            }
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            print("✅ Login successful")
            print(f"   Token: {self.token[:50]}...")
            return True
        else:
            self.print_result("User Login", False, response)
            return False

    def test_protected_endpoints(self):
        print("\n🛡️ Testing Protected Endpoints")
        print("-" * 40)

        if not self.token:
            print("❌ No token available")
            return False

        headers = {"Authorization": f"Bearer {self.token}"}
        endpoints = [
            ("Get Current User", "GET", "/api/v1/auth/me"),
            ("Get Subscriptions", "GET", "/api/v1/subscriptions"),
            ("Get Payment History", "GET", "/api/v1/payments/history"),
            ("Get Invoices", "GET", "/api/v1/billing/invoices"),
        ]

        all_success = True

        for name, method, endpoint in endpoints:
            print(f"\n   Testing {name}...")
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", headers=headers)

                if response.status_code == 200:
                    print(f"     ✅ {name}: Success")
                    data = response.json()
                    if isinstance(data, list):
                        print(f"       Found {len(data)} items")
                    elif isinstance(data, dict):
                        print(f"       User: {data.get('username', 'Unknown')}")
                elif response.status_code == 404:
                    print(f"     ⚠️ {name}: Not found (normal for empty data)")
                else:
                    print(f"     ❌ {name}: Failed (Status: {response.status_code})")
                    print(f"       Error: {response.text[:100]}")
                    all_success = False

            except Exception as e:
                print(f"     ❌ {name}: Error - {e}")
                all_success = False

        return all_success

    def test_subscription_flow(self):
        print("\n🛒 Testing Subscription Flow")
        print("-" * 40)

        if not self.token:
            print("❌ No token available")
            return False

        headers = {"Authorization": f"Bearer {self.token}"}

        # Get plans
        response = requests.get(f"{self.base_url}/api/v1/plans")
        if response.status_code != 200:
            print("❌ Cannot get plans")
            return False

        plans = response.json()
        if not plans:
            print("❌ No plans available")
            return False

        # Try to create subscription (use Pro plan - usually id=2)
        pro_plan = None
        for plan in plans:
            if "pro" in plan["name"].lower() or plan["price"] > 0:
                pro_plan = plan
                break

        if not pro_plan:
            pro_plan = plans[1] if len(plans) > 1 else plans[0]

        print(f"   Attempting to subscribe to: {pro_plan['name']} (₹{pro_plan['price'] / 100})")

        response = requests.post(
            f"{self.base_url}/api/v1/subscriptions/create",
            json={"plan_id": pro_plan["id"]},
            headers=headers
        )

        if response.status_code == 200:
            print("   ✅ Subscription created successfully")
            return True
        elif response.status_code == 400 and "already has active subscription" in response.text.lower():
            print("   ⚠️ User already has active subscription (normal)")
            return True
        else:
            print(f"   ❌ Subscription creation failed: {response.status_code}")
            print(f"     Error: {response.text[:200]}")
            return False

    def run_all_tests(self):
        print("🚀 Running Complete API Test Suite")
        print("=" * 60)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        results = {}

        # Basic tests
        results["health"] = self.test_health()
        results["plans"] = self.test_plans()

        # Auth tests
        if results["plans"]:
            results["register"] = self.create_test_user()
        else:
            results["register"] = False

        if results.get("register"):
            results["login"] = self.login_user()
        else:
            results["login"] = False

        # Protected endpoints
        if results.get("login"):
            results["protected"] = self.test_protected_endpoints()
            results["subscription"] = self.test_subscription_flow()
        else:
            results["protected"] = False
            results["subscription"] = False

        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for result in results.values() if result)
        total = len(results)

        for name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {name.replace('_', ' ').title()}")

        print("\n" + "=" * 60)
        print(f"🎯 Total: {passed}/{total} tests passed ({passed / total * 100:.1f}%)")

        if passed == total:
            print("\n🎉 All tests passed! API is working correctly.")
        elif passed >= total * 0.7:
            print(f"\n⚠️ {passed}/{total} tests passed. Some minor issues.")
        else:
            print(f"\n❌ Only {passed}/{total} tests passed. Needs attention.")

        return results


if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()