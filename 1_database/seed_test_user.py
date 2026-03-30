"""
Seed a test user with hashed password for TerraGuard login testing.
Run from project root: python 1_database/seed_test_user.py

Requires: DB connection working. If you get Access denied, fix Aiven:
  1. Aiven Console > MySQL service > Add your IP (103.72.222.44) to allowlist
  2. Reset password in Aiven, update DB_PASSWORD in .env
"""
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.security import generate_password_hash
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

CA_CERT_PATH = os.path.join(BASE_DIR, "4_frontend_app", "ca.pem")

user = (os.getenv("DB_USER") or "avnadmin").strip()
password = (os.getenv("DB_PASSWORD") or "").strip().strip("\r")
host = (os.getenv("DB_HOST") or "terraguard-db-project-e68.a.aivencloud.com").strip()
port = (os.getenv("DB_PORT") or "20095").strip()
db_name = "defaultdb"

if not password:
    print("ERROR: DB_PASSWORD not set in .env. Add your Aiven password.")
    sys.exit(1)

safe_password = urllib.parse.quote_plus(password)
conn_str = f"mysql+pymysql://{user}:{safe_password}@{host}:{port}/{db_name}"
engine = create_engine(conn_str, connect_args={"ssl": {"ca": CA_CERT_PATH}})

# Create test users
hashed = generate_password_hash("test123")

try:
    with engine.begin() as conn:
        conn.execute(text("USE TerraGuard_DB"))
        conn.execute(text("""
            INSERT INTO Users (name, phone_number, password_hash, role_id)
            VALUES ('Test Civilian', '9876543210', :hash, 1)
            ON DUPLICATE KEY UPDATE password_hash = :hash2
        """), {"hash": hashed, "hash2": hashed})
        conn.execute(text("""
            INSERT INTO Users (name, phone_number, password_hash, role_id)
            VALUES ('Test Agency', '9876543211', :hash, 2)
            ON DUPLICATE KEY UPDATE password_hash = :hash2
        """), {"hash": hashed, "hash2": hashed})
except Exception as e:
    print("\n--- Database connection failed ---")
    print(str(e))
    print("\n>>> USE THE APP NOW (no DB needed):")
    print("    Add to .env:  TERRAGUARD_DEV_MODE=1")
    print("    Login with:  9876543210 / test123  (Civilian)")
    print("                9876543211 / test123  (Agency)")
    print("\n>>> To fix DB for real data later:")
    print("  1. Aiven Console > MySQL service > IP allowlist")
    print("     Add: 103.72.222.44 (or 0.0.0.0/0)")
    print("  2. Aiven > Overview > Reset password")
    print("  3. Update DB_PASSWORD in .env, set TERRAGUARD_DEV_MODE=0")
    print("  4. Run this script again\n")
    sys.exit(1)

print("Test users created: 9876543210 (Civilian), 9876543211 (Agency). Password: test123")
