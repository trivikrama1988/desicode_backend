"""Test configuration and server fixture.

This module selects a free port at import time (unless TEST_PORT is set) and
exports TEST_BASE_URL so other test modules read the dynamic URL during import.
"""

import os
import socket
import subprocess
import sys
import time
import requests
import pytest

# Determine port early so test modules see TEST_BASE_URL during import
port = int(os.environ.get("TEST_PORT", 0))
if port == 0:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()

TEST_BASE_URL = os.environ.get("TEST_BASE_URL", f"http://127.0.0.1:{port}")
os.environ["TEST_PORT"] = str(port)
os.environ["TEST_BASE_URL"] = TEST_BASE_URL

BASE_URL = TEST_BASE_URL

LOG_PATH = os.path.join(os.path.dirname(__file__), "uvicorn_test.log")

@pytest.fixture(scope="session", autouse=True)
def server():
    """Start a uvicorn server for the app for the duration of the tests."""
    # Ensure old log removed
    try:
        os.remove(LOG_PATH)
    except Exception:
        pass

    # Determine port to use: prefer TEST_PORT env var, otherwise pick a free port
    port = int(os.environ.get("TEST_PORT", 8000))
    # Use the TEST_BASE_URL already set at import time
    base_url = os.environ.get("TEST_BASE_URL")

    # Start uvicorn as a subprocess and capture output to log
    cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port), "--log-level", "debug"]
    # Ensure PYTHONPATH includes the current directory so `app` package is importable
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(os.getcwd())
    with open(LOG_PATH, "wb") as logf:
        proc = subprocess.Popen(cmd, stdout=logf, stderr=logf, env=env)

    # Wait for server to be ready
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            r = requests.get(f"{BASE_URL}/")
            if r.status_code in (200, 404):
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(0.2)
    else:
        # Read log for diagnostics
        try:
            with open(LOG_PATH, "r", encoding="utf-8", errors="replace") as f:
                log = f.read()
        except Exception:
            log = "(could not read uvicorn log)"
        proc.terminate()
        raise RuntimeError(f"Test server did not start in time. Uvicorn log:\n{log}")

    yield

    # Teardown
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()


@pytest.fixture(scope="session")
def token(server):
    """Register or login a test user and return an access token (or raise).

    This fixture retries a few times to work around transient startup races.
    """
    max_attempts = 4
    backoff = 0.5

    for attempt in range(1, max_attempts + 1):
        # Generate unique user data for each attempt
        timestamp = int(time.time()) + attempt  # Make each attempt unique
        register_data = {
            "username": f"pytest_user_{timestamp}",
            "email": f"pytest_{timestamp}@example.com",
            "password": "Test123!"
        }

        try:
            # Try to register the user
            r = requests.post(f"{BASE_URL}/api/auth/register", json=register_data, timeout=10)

            # If registered successfully, return the token
            if r and r.status_code == 201:
                try:
                    token = r.json().get("access_token")
                    if token:
                        return token
                except Exception:
                    pass

            # If user exists (400), try to login
            elif r and r.status_code == 400:
                try:
                    login_data = {"email": register_data["email"], "password": register_data["password"]}
                    r2 = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, timeout=10)
                    if r2 and r2.status_code == 200:
                        token = r2.json().get("access_token")
                        if token:
                            return token
                except Exception:
                    pass

            # For any other response, log the error for debugging
            if r:
                print(f"Token fixture attempt {attempt}: {r.status_code} - {r.text[:200]}")

        except Exception as exc:
            print(f"Token fixture attempt {attempt} exception: {exc}")

        # Wait before retry (except on last attempt)
        if attempt < max_attempts:
            time.sleep(backoff * attempt)

    # If we reach here, attempts failed. Capture uvicorn log for diagnostics and fail loudly.
    try:
        with open(LOG_PATH, "r", encoding="utf-8", errors="replace") as f:
            log = f.read()
    except Exception:
        log = "(could not read uvicorn log)"

    raise RuntimeError(f"Could not obtain test token after {max_attempts} attempts. Uvicorn log:\n{log}")
