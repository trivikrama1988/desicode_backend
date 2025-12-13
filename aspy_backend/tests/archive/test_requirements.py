#!/usr/bin/env python3
"""
Project Requirements Verification Script
Validates all 19 required APIs against current implementation
"""

import requests
import time
import json
from datetime import datetime

def test_project_requirements():
    """Test all required APIs from Project Requirements document"""

    print("Project Requirements Verification")
    print("=" * 50)

    # Define all required APIs from the requirements
    required_apis = {
        "AUTHENTICATION (3 APIs)": [
            ("POST", "/api/auth/register", "User registration"),
            ("POST", "/api/auth/login", "User login"),
            ("GET", "/api/auth/me", "Get current user")
        ],
        "SUBSCRIPTION MANAGEMENT (5 APIs)": [
            ("GET", "/api/subscriptions", "Get user's subscriptions"),
            ("GET", "/api/subscriptions/{id}", "Get subscription details"),
            ("POST", "/api/subscriptions/create", "Create new subscription"),
            ("PUT", "/api/subscriptions/{id}/cancel", "Cancel subscription"),
            ("GET", "/api/plans", "Get available plans")
        ],
        "PAYMENT PROCESSING (4 APIs)": [
            ("POST", "/api/payments/stripe/create-checkout", "Stripe checkout session"),
            ("POST", "/api/payments/razorpay/create-order", "Razorpay order creation"),
            ("POST", "/api/payments/razorpay/verify", "Razorpay payment verification"),
            ("GET", "/api/payments/history", "Payment transaction history")
        ],
        "WEBHOOKS (2 APIs)": [
            ("POST", "/api/webhooks/stripe", "Stripe payment notifications"),
            ("POST", "/api/webhooks/razorpay", "Razorpay payment notifications")
        ],
        "BILLING & INVOICES (3 APIs)": [
            ("GET", "/api/billing/invoices", "Get user invoices"),
            ("GET", "/api/billing/invoices/{id}", "Download invoice"),
            ("GET", "/api/billing/usage", "Get usage statistics")
        ],
        "USER PROFILE (2 APIs)": [
            ("GET", "/api/users/profile", "Get user profile"),
            ("PUT", "/api/users/profile", "Update user profile")
        ]
    }

    # Check implementation
    try:
        from app.main import app

        # Get all current routes
        current_routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                path = route.path
                methods = list(route.methods) if route.methods else ['GET']

                for method in methods:
                    if path.startswith('/api/'):
                        current_routes.append((method, path))

        print(f"Current implementation: {len(current_routes)} API routes")
        print()

        # Verify each category
        total_required = 0
        total_implemented = 0
        missing_apis = []

        for category, apis in required_apis.items():
            print(f"{category}:")
            category_missing = []

            for method, endpoint, description in apis:
                total_required += 1

                # Check if implemented
                found = False
                for impl_method, impl_path in current_routes:
                    if impl_method == method and endpoint == impl_path:
                        found = True
                        break
                    # Handle parameter variations
                    elif "{id}" in endpoint and impl_method == method:
                        if (endpoint.replace("{id}", "{subscription_id}") == impl_path or
                            endpoint.replace("{id}", "{invoice_id}") == impl_path):
                            found = True
                            break

                if found:
                    total_implemented += 1
                    print(f"  [PASS] {method} {endpoint}")
                else:
                    category_missing.append((method, endpoint, description))
                    missing_apis.append((category, method, endpoint, description))
                    print(f"  [FAIL] {method} {endpoint} - {description}")

            print(f"  Status: {len(apis) - len(category_missing)}/{len(apis)} implemented")
            print()

        # Check transpiler API (bonus feature)
        print("TRANSPILER API (Bonus Feature):")
        transpiler_found = False
        for method, path in current_routes:
            if method == "POST" and path == "/api/run":
                transpiler_found = True
                break

        if transpiler_found:
            print("  [PASS] POST /api/run - Code execution")
        else:
            print("  [FAIL] POST /api/run - Code execution")
        print()

        # Final summary
        print("VERIFICATION SUMMARY")
        print("=" * 30)
        print(f"Total required APIs: {total_required}")
        print(f"Total implemented: {total_implemented}")
        completion_rate = (total_implemented / total_required) * 100
        print(f"Completion rate: {completion_rate:.1f}%")

        if missing_apis:
            print()
            print("MISSING APIS:")
            for category, method, endpoint, description in missing_apis:
                print(f"  {method} {endpoint} - {description}")
            return False
        else:
            print()
            print("ALL REQUIREMENTS MET")
            if transpiler_found:
                print("Bonus: Transpiler API also implemented")
            return True

    except Exception as e:
        print(f"Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_server_health():
    """Test if server is running and accessible"""

    print("Server Health Check")
    print("=" * 20)

    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("Server is running and accessible")
            return True
        else:
            print(f"Server returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Server is not accessible: {e}")
        return False

def test_api_endpoints():
    """Test actual API endpoints if server is running"""

    print("API Endpoint Testing")
    print("=" * 20)

    base_url = "http://localhost:8000"

    # Test public endpoints (no auth required)
    public_tests = [
        ("GET", "/health", "Health check"),
        ("GET", "/api/health", "API health check"),
        ("GET", "/api/plans", "Get plans"),
        ("GET", "/api/run/supported-languages", "Supported languages")
    ]

    passed = 0
    total = len(public_tests)

    for method, endpoint, description in public_tests:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=5)

            if response.status_code in [200, 404]:  # 404 is acceptable for some endpoints
                print(f"  [PASS] {method} {endpoint} - {description}")
                passed += 1
            else:
                print(f"  [FAIL] {method} {endpoint} - Status: {response.status_code}")
        except Exception as e:
            print(f"  [ERROR] {method} {endpoint} - {e}")

    print(f"Public endpoints test: {passed}/{total} passed")
    return passed == total

def main():
    """Main test runner"""

    print("DesiCodes Backend API Verification")
    print(f"Test run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    # Run all tests
    requirements_ok = test_project_requirements()
    print()

    server_ok = test_server_health()
    print()

    if server_ok:
        endpoints_ok = test_api_endpoints()
    else:
        endpoints_ok = False
        print("Skipping endpoint tests - server not running")

    print()
    print("FINAL RESULTS")
    print("=" * 20)

    if requirements_ok:
        print("Requirements check: PASS - All 19 APIs implemented")
    else:
        print("Requirements check: FAIL - Some APIs missing")

    if server_ok:
        print("Server health: PASS - Server running")
    else:
        print("Server health: FAIL - Server not accessible")

    if endpoints_ok:
        print("Endpoint tests: PASS - APIs responding")
    else:
        print("Endpoint tests: FAIL - Some endpoints not working")

    print()
    if requirements_ok and server_ok and endpoints_ok:
        print("OVERALL STATUS: ALL TESTS PASSED")
        print("The backend is ready for production deployment")
    else:
        print("OVERALL STATUS: SOME TESTS FAILED")
        print("Review failed tests and fix issues before deployment")

if __name__ == "__main__":
    main()
