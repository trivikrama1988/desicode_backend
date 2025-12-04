import requests

BASE_URL = "http://localhost:8000"


def quick_test():
    print("Quick Smoke Test for ASPY Backend")
    print("=" * 50)

    # Test 1: Health check
    try:
        health = requests.get(f"{BASE_URL}/health")
        print(f"Ok  Health: {health.status_code} - {health.json()}")
    except:
        print(f"Failure Health: Cannot connect to {BASE_URL}")
        return

    # Test 2: Get plans
    plans = requests.get(f"{BASE_URL}/api/v1/plans")
    if plans.status_code == 200:
        data = plans.json()
        print(f"Ok  Plans: Found {len(data)} plans")
        for plan in data:
            print(f"   - {plan['name']}: ${plan['price'] / 100}")
    else:
        print(f"Failure Plans: {plans.status_code} - {plans.text}")

    # Test 3: Create test user
    import random
    email = f"test{random.randint(1000, 9999)}@test.com"
    user_data = {
        "username": f"testuser{random.randint(1000, 9999)}",
        "email": email,
        "password": "TestPass123!"
    }

    register = requests.post(f"{BASE_URL}/api/v1/auth/register", json=user_data)
    if register.status_code == 201:
        print(f"Ok  Registration: User created ({user_data['email']})")
    else:
        print(f"Failure Registration: {register.status_code} - {register.text}")
        return

    # Test 4: Login
    login_data = {
        "email": email,
        "password": "TestPass123!"
    }
    login = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    if login.status_code == 200:
        token = login.json().get("access_token")
        print(f"Ok  Login: Success, got token")
    else:
        print(f"Failure Login: {login.status_code} - {login.text}")
        return

    # Test 5: Get profile with token
    headers = {"Authorization": f"Bearer {token}"}
    profile = requests.get(f"{BASE_URL}/api/v1/users/profile", headers=headers)
    if profile.status_code == 200:
        print(f"Ok  Profile: {profile.json()['username']}")
    else:
        print(f"Failure Profile: {profile.status_code} - {profile.text}")

    print("\n" + "=" * 50)
    print(" Quick test completed!")


if __name__ == "__main__":
    quick_test()