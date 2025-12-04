import requests
import json

BASE_URL = "http://localhost:8000"


class AdminTester:
    def __init__(self, admin_token=None):
        self.headers = {"Content-Type": "application/json"}
        if admin_token:
            self.headers["Authorization"] = f"Bearer {admin_token}"

    def create_admin_user(self):
        """Create an admin user for testing"""
        data = {
            "username": "admin",
            "email": "admin@aspy.com",
            "password": "AdminPass123!"
        }
        response = requests.post(f"{BASE_URL}/api/v1/auth/register",
                                 json=data, headers=self.headers)
        return response

    def list_all_users(self):
        """Get all users (requires admin endpoint - you'd need to implement this)"""
        # Note: You need to add admin endpoints first
        response = requests.get(f"{BASE_URL}/api/v1/admin/users", headers=self.headers)
        return response

    def seed_test_data(self):
        """Seed test data including users, subscriptions, etc."""
        print("Seeding test data...")

        # Create multiple test users
        test_users = []
        for i in range(3):
            user_data = {
                "username": f"tester{i}",
                "email": f"tester{i}@test.com",
                "password": f"TestPass{i}!"
            }
            resp = requests.post(f"{BASE_URL}/api/v1/auth/register",
                                 json=user_data, headers=self.headers)
            if resp.status_code == 201:
                test_users.append(resp.json())
                print(f"Created user: tester{i}")

        return test_users


def main():
    tester = AdminTester()

    print("Tool  Admin Test Suite")
    print("=" * 50)

    # Create admin user
    print("\n1. Creating admin user...")
    response = tester.create_admin_user()
    if response.status_code == 201:
        print("Ok  Admin user created")
        admin_data = response.json()
        print(f"   ID: {admin_data['id']}")
        print(f"   Email: {admin_data['email']}")
    else:
        print(f" Failed: {response.status_code} - {response.text}")

    # Seed test data
    print("\n2. Seeding test data...")
    users = tester.seed_test_data()
    print(f"Ok  Created {len(users)} test users")


if __name__ == "__main__":
    main()