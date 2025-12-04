# test_connection.py
import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        database="aspy_db",
        user="postgres",
        password="aspy1234"  # Try empty, then your password
    )
    print("✅ Connected successfully!")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")