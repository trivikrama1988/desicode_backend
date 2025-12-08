import requests
import json


def debug_api_endpoints():
    BASE_URL = "http://localhost:8000"

    print("Debugging API Endpoints")
    print("=" * 50)

    endpoints = [
        ("/api/v1/plans", "GET"),
        ("/api/v1/subscriptions", "GET"),
    ]

    for endpoint, method in endpoints:
        print(f"\nTesting: {endpoint}")
        print("-" * 30)

        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")

            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")

            try:
                data = response.json()
                print(f"Response JSON: {json.dumps(data, indent=2)}")
            except:
                print(f"Response Text: {response.text[:500]}")

        except Exception as e:
            print(f"Error: {e}")


def test_plans_with_auth():
    """Test plans endpoint with authentication"""
    print("\n\nTesting Plans with Authentication")
    print("=" * 50)

    # First create a test user and login
    timestamp = 1765214322  # Use the timestamp from your error

    # Register
    register_data = {
        "username": f"debug_user_{timestamp}",
        "email": f"debug_{timestamp}@test.com",
        "password": "Test123!"
    }

    response = requests.post("http://localhost:8000/api/v1/auth/register", json=register_data)
    print(f"Register Status: {response.status_code}")

    if response.status_code == 201:
        # Login
        login_data = {
            "email": register_data["email"],
            "password": register_data["password"]
        }

        response = requests.post("http://localhost:8000/api/v1/auth/login", json=login_data)
        print(f"Login Status: {response.status_code}")

        if response.status_code == 200:
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Test plans endpoint with auth
            response = requests.get("http://localhost:8000/api/v1/plans", headers=headers)
            print(f"\nPlans with Auth - Status: {response.status_code}")
            print(f"Response: {response.text[:500]}")


if __name__ == "__main__":
    debug_api_endpoints()
    test_plans_with_auth()