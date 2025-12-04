import requests
import time
import concurrent.futures
from threading import Thread

BASE_URL = "http://localhost:8000"


def stress_test_concurrent_users(num_users=10):
    """Test concurrent user registrations and logins"""
    print(f"Stress Test: Simulating {num_users} concurrent users")
    print("=" * 60)

    def register_and_login(user_id):
        email = f"stress{user_id}_{int(time.time())}@test.com"
        username = f"stressuser{user_id}"
        password = "StressPass123!"

        # Register
        start = time.time()
        register_data = {
            "username": username,
            "email": email,
            "password": password
        }
        register_resp = requests.post(f"{BASE_URL}/api/v1/auth/register",
                                      json=register_data)
        register_time = time.time() - start

        # Login
        start = time.time()
        login_data = {
            "email": email,
            "password": password
        }
        login_resp = requests.post(f"{BASE_URL}/api/v1/auth/login",
                                   json=login_data)
        login_time = time.time() - start

        return {
            "user_id": user_id,
            "register_time": register_time,
            "login_time": login_time,
            "register_success": register_resp.status_code == 201,
            "login_success": login_resp.status_code == 200
        }

    # Run concurrent tests
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
        futures = [executor.submit(register_and_login, i) for i in range(num_users)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]

    total_time = time.time() - start_time

    # Calculate statistics
    successful_registrations = sum(1 for r in results if r["register_success"])
    successful_logins = sum(1 for r in results if r["login_success"])
    avg_register_time = sum(r["register_time"] for r in results) / len(results)
    avg_login_time = sum(r["login_time"] for r in results) / len(results)

    print(f"\n   Results:")
    print(f"   Total Time: {total_time:.2f} seconds")
    print(f"   Successful Registrations: {successful_registrations}/{num_users}")
    print(f"   Successful Logins: {successful_logins}/{num_users}")
    print(f"   Average Registration Time: {avg_register_time:.3f}s")
    print(f"   Average Login Time: {avg_login_time:.3f}s")
    print(f"   Requests per Second: {num_users * 2 / total_time:.2f}")

    return results


def api_endpoint_benchmark(endpoint, method="GET", data=None, num_requests=100):
    """Benchmark a specific API endpoint"""
    print(f"\n⚡ Benchmarking {method} {endpoint}")

    times = []
    successful = 0

    for i in range(num_requests):
        start = time.time()
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}", json=data)

            elapsed = time.time() - start
            times.append(elapsed)

            if response.status_code < 400:
                successful += 1
        except Exception as e:
            times.append(0)

    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        success_rate = successful / num_requests * 100

        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Average Response Time: {avg_time * 1000:.2f}ms")
        print(f"   Min Response Time: {min_time * 1000:.2f}ms")
        print(f"   Max Response Time: {max_time * 1000:.2f}ms")
        print(f"   Requests per Second: {1 / avg_time if avg_time > 0 else 0:.2f}")

    return times


if __name__ == "__main__":
    print("🔬 API Stress Test & Benchmark")
    print("=" * 60)

    # Test 1: Basic endpoints benchmark
    print("\n1. Basic Endpoints Benchmark (10 requests each):")
    api_endpoint_benchmark("/health", num_requests=10)
    api_endpoint_benchmark("/", num_requests=10)
    api_endpoint_benchmark("/api/v1/plans", num_requests=10)

    # Test 2: Stress test with concurrent users
    print("\n2. Concurrent User Test (5 users):")
    stress_test_concurrent_users(5)

    print("\nAll Stress test completed!")