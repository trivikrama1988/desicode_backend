# test_transpiler_api.py
import requests
import json
import sys
import pytest
import os

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8000")


def test_health():
    """Test health endpoint"""
    print("\nTesting health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    # Assert healthy status
    assert response.status_code == 200


def test_root():
    """Test root endpoint"""
    print("\nTesting root endpoint...")
    response = requests.get(BASE_URL)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200


def test_supported_languages():
    """Test supported languages endpoint"""
    print("\nTesting supported languages endpoint...")
    response = requests.get(f"{BASE_URL}/api/run/supported-languages")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {data.get('count', 0)} languages:")
        for lang in data.get('languages', []):
            print(f"  - {lang['name']} ({lang['code']})")
    else:
        print(f"Error: {response.text}")
    assert response.status_code == 200


def test_auth():
    """Test authentication (register or login)"""
    print("\nTesting authentication...")

    # Try to register a test user
    register_data = {
        "username": "apitestuser",
        "email": "apitest@example.com",
        "password": "ApiTest@123"
    }

    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)

    if response.status_code == 201:
        print("Registered new user")
        data = response.json()
        token = data.get('access_token')
        assert token
    elif response.status_code == 400 and "already registered" in response.text:
        # User exists, try login
        print("User already exists, trying login...")
        login_data = {
            "email": "apitest@example.com",
            "password": "ApiTest@123"
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            assert token
        else:
            pytest.fail(f"Login failed: {response.text}")
    else:
        pytest.fail(f"Registration failed: {response.text}")


def test_run_code(token):
    """Test code execution with authentication"""
    print("\nTesting code execution...")

    if not token:
        pytest.skip("No token available from fixture; skipping execution test")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # First check quota
    print("Checking quota...")
    response = requests.get(f"{BASE_URL}/api/run/quota", headers=headers)
    if response.status_code == 200:
        quota = response.json()
        print(f"Quota: {quota.get('quota_remaining')}/{quota.get('monthly_quota')} remaining")
    else:
        print(f" Quota check failed: {response.text}")
        # Continue anyway

    # Test with simple code
    test_data = {
        "code": "print('Hello from Python!')",
        "language": "assamese",
        "timeout": 5
    }

    print("\nExecuting code...")
    response = requests.post(
        f"{BASE_URL}/api/run",
        headers=headers,
        json=test_data,
        timeout=10
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result.get('success')}")
        print(f"Execution time: {result.get('execution_time', 0):.2f}s")
        print(f"Language: {result.get('language')}")

        if result.get('errors'):
            print(f"Errors: {result.get('errors')[:200]}...")

        if result.get('output'):
            output = result.get('output', '')
            print(f"Output: {output[:200]}{'...' if len(output) > 200 else ''}")

        if result.get('transpiled_code'):
            transpiled = result.get('transpiled_code', '')
            print(f"Transpiled code preview: {transpiled[:200]}{'...' if len(transpiled) > 200 else ''}")

        print(f"Quota remaining: {result.get('quota_remaining')}")
        print(f"Execution ID: {result.get('execution_id')}")

        # Basic assertions about response structure
        assert 'success' in result
        assert 'execution_id' in result
    elif response.status_code in (403, 429, 408):
        # allowed non-success outcomes depending on subscription/quota/timeouts
        pytest.skip(f"Server returned status {response.status_code}; skipping assertions")
    else:
        pytest.fail(f"Unexpected error from /api/run: {response.status_code} - {response.text}")


def test_execution_history(token):
    """Test execution history"""
    print("\nTesting execution history...")

    if not token:
        pytest.skip("No token available from fixture; skipping history test")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.get(f"{BASE_URL}/api/run/history", headers=headers)

    if response.status_code == 200:
        history = response.json()
        print(f"History: {history.get('total', 0)} total executions")
        print(f"Showing {len(history.get('history', []))} recent executions")

        for i, exec_item in enumerate(history.get('history', [])[:3]):  # Show first 3
            print(f"\n  Execution {i + 1}:")
            print(f"    ID: {exec_item.get('execution_id')}")
            print(f"    Language: {exec_item.get('language')}")
            print(f"    Success: {exec_item.get('success')}")
            print(f"    Time: {exec_item.get('execution_time_ms', 0)}ms")
            print(f"    Created: {exec_item.get('created_at')}")

        assert isinstance(history.get('history', []), list)
    else:
        pytest.fail(f"History check failed: {response.text}")


def main():
    """Run all tests"""
    print("Starting DesiCodes Transpiler API Tests")
    print("=" * 50)

    # Check if server is running
    try:
        response = requests.get(BASE_URL, timeout=2)
        print(f"Server is running at {BASE_URL}")
    except Exception as e:
        print(f" Server not running at {BASE_URL}")
        print(f"Error: {e}")
        print("Please start the server with: uvicorn app.main:app --reload")
        sys.exit(1)

    # Run tests
    results = []

    # Test basic endpoints
    print(f"\n{'=' * 50}")
    print("Basic Endpoints")
    print(f"{'=' * 50}")

    for test_name, test_func in [
        ("Health Check", test_health),
        ("Root Endpoint", test_root),
        ("Supported Languages", test_supported_languages),
    ]:
        try:
            print(f"\n{test_name}...")
            success = test_func()
            results.append((test_name, success))
            print(f"{test_name} passed" if success else f" {test_name} failed")
        except Exception as e:
            print(f" {test_name} failed with error: {e}")
            results.append((test_name, False))

    # Test authentication
    print(f"\n{'=' * 50}")
    print("Authentication")
    print(f"{'=' * 50}")

    token = test_auth()
    auth_success = token is not None
    results.append(("Authentication", auth_success))

    if auth_success:
        # Test authenticated endpoints
        print(f"\n{'=' * 50}")
        print("Authenticated Endpoints")
        print(f"{'=' * 50}")

        for test_name, test_func in [
            ("Code Execution", lambda: test_run_code(token)),
            ("Execution History", lambda: test_execution_history(token)),
        ]:
            try:
                print(f"\n{test_name}...")
                success = test_func()
                results.append((test_name, success))
                print(f"{test_name} passed" if success else f" {test_name} failed")
            except Exception as e:
                print(f" {test_name} failed with error: {e}")
                results.append((test_name, False))

    # Print summary
    print(f"\n{'=' * 50}")
    print("Test Summary")
    print(f"{'=' * 50}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "PASS" if success else " FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\nAll tests passed! API is working correctly.")
    else:
        print(f"\n{total - passed} test(s) failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
