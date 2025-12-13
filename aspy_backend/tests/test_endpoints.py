import requests
import json
import time
from datetime import datetime
import pytest


class APITester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.token = None
        self.user_data = None

    def print_result(self, test_name, success, response=None):
        if success:
            print(f"{test_name}: PASSED")
        else:
            print(f"{test_name}: FAILED")
            if response:
                print(f"   Status: {response.status_code}")
                print(f"   Error: {response.text[:200]}")

    def test_health(self):
        print("\n🔍 Testing Health Endpoint")
        print("-" * 40)
        response = requests.get(f"{self.base_url}/health")
        assert response.status_code == 200, f"Health check failed: {response.status_code} {response.text}"

    def test_plans(self):
        print("\nTesting Plans Endpoint")
        print("-" * 40)
        response = requests.get(f"{self.base_url}/api/plans")
        assert response.status_code == 200, f"Plans endpoint returned: {response.status_code} {response.text}"

        plans = response.json()
        print(f"Found {len(plans)} plans:")
        for plan in plans:
            print(f"   • {plan['name']}: ₹{plan['price'] / 100}")

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
            f"{self.base_url}/api/auth/register",
            json=self.user_data
        )

        assert response.status_code == 201, f"User registration failed: {response.status_code} {response.text}"
        print(f"User created: {self.user_data['email']}")

    def login_user(self):
        print("\nTesting User Login")
        print("-" * 40)

        response = requests.post(
            f"{self.base_url}/api/auth/login",
            json={
                "email": self.user_data["email"],
                "password": self.user_data["password"]
            }
        )

        assert response.status_code == 200, f"Login failed: {response.status_code} {response.text}"
        data = response.json()
        self.token = data["access_token"]
        print("Login successful")
        print(f"   Token: {self.token[:50]}...")

    def test_protected_endpoints(self):
        print("\nTesting Protected Endpoints")
        print("-" * 40)

        assert self.token, "No token available"

        headers = {"Authorization": f"Bearer {self.token}"}
        endpoints = [
            ("Get Current User", "GET", "/api/auth/me"),
            ("Get Subscriptions", "GET", "/api/subscriptions"),
            ("Get Payment History", "GET", "/api/payments/history"),
            ("Get Invoices", "GET", "/api/billing/invoices"),
        ]

        for name, method, endpoint in endpoints:
            print(f"\n   Testing {name}...")
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", headers=headers)

                if response.status_code == 200:
                    print(f"     {name}: Success")
                    data = response.json()
                    if isinstance(data, list):
                        print(f"       Found {len(data)} items")
                    elif isinstance(data, dict):
                        print(f"       User: {data.get('username', 'Unknown')}")
                elif response.status_code == 404:
                    print(f"  {name}: Not found (normal for empty data)")
                else:
                    pytest.fail(f"{name} failed: {response.status_code} {response.text}")

            except Exception as e:
                pytest.fail(f"{name} Error - {e}")

    def test_subscription_flow(self):
        print("\n🛒 Testing Subscription Flow")
        print("-" * 40)

        assert self.token, "No token available"

        headers = {"Authorization": f"Bearer {self.token}"}

        # Get plans
        response = requests.get(f"{self.base_url}/api/plans")
        assert response.status_code == 200, "Cannot get plans"

        plans = response.json()
        assert plans, "No plans available"

        # Choose a pro plan if available
        pro_plan = None
        for plan in plans:
            if "pro" in plan["name"].lower() or plan["price"] > 0:
                pro_plan = plan
                break

        if not pro_plan:
            pro_plan = plans[1] if len(plans) > 1 else plans[0]

        print(f"   Attempting to subscribe to: {pro_plan['name']} (₹{pro_plan['price'] / 100})")

        response = requests.post(
            f"{self.base_url}/api/subscriptions/create",
            json={"plan_id": pro_plan["id"]},
            headers=headers
        )

        if response.status_code == 200:
            print("   Subscription created successfully")
        elif response.status_code == 400 and "already has active subscription" in response.text.lower():
            print("User already has active subscription (normal)")
        else:
            pytest.fail(f"Subscription creation failed: {response.status_code} {response.text}")

    def run_all_tests(self):
        print("Running Complete API Test Suite")
        print("=" * 60)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        results = {}

        # Basic tests
        try:
            self.test_health()
            results['health'] = True
        except AssertionError as e:
            results['health'] = False
            print(e)

        try:
            self.test_plans()
            results['plans'] = True
        except AssertionError as e:
            results['plans'] = False
            print(e)

        # Auth tests
        if results['plans']:
            try:
                self.create_test_user()
                results['register'] = True
            except AssertionError as e:
                results['register'] = False
                print(e)
        else:
            results['register'] = False

        if results.get('register'):
            try:
                self.login_user()
                results['login'] = True
            except AssertionError as e:
                results['login'] = False
                print(e)
        else:
            results['login'] = False

        # Protected endpoints
        if results.get('login'):
            try:
                self.test_protected_endpoints()
                results['protected'] = True
            except AssertionError as e:
                results['protected'] = False
                print(e)
            try:
                self.test_subscription_flow()
                results['subscription'] = True
            except AssertionError as e:
                results['subscription'] = False
                print(e)
        else:
            results['protected'] = False
            results['subscription'] = False

        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for result in results.values() if result)
        total = len(results)

        for name, result in results.items():
            status = "PASS" if result else "FAIL"
            print(f"{status} {name.replace('_', ' ').title()}")

        print("\n" + "=" * 60)
        print(f"Total: {passed}/{total} tests passed ({passed / total * 100:.1f}%)")

        if passed == total:
            print("\nAll tests passed! API is working correctly.")
        elif passed >= total * 0.7:
            print(f"\n{passed}/{total} tests passed. Some minor issues.")
        else:
            print(f"\nOnly {passed}/{total} tests passed. Needs attention.")

        return results


if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()
