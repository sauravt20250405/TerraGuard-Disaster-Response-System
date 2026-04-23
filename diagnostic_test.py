import os
import urllib.parse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("DB_HOST", "").strip()
port = os.getenv("DB_PORT", "").strip()
user = os.getenv("DB_USER", "").strip()
password = os.getenv("DB_PASSWORD", "").strip()
dbname = os.getenv("DB_NAME", "").strip()

print(f"DEBUG: Attempting connection to {host}:{port} for user {user} on db {dbname}")
print(f"DEBUG: Password: {password}")

# Bypassing quote_plus if needed
if "pooler.supabase.com" in host or port == "5432" or port == "6543":
    db_uri = f"postgresql+psycopg2://{user}:{urllib.parse.quote_plus(password)}@{host}:{port}/{dbname}"
    try:
        print("Trying with PostgreSQL (Supabase Pooler)...")
        engine = create_engine(db_uri, pool_pre_ping=True, connect_args={"connect_timeout": 10})
        with engine.connect() as conn:
            res = conn.execute(text("SELECT 1")).scalar()
            print(f"SUCCESS (PostgreSQL): {res}")
            exit(0)
    except Exception as e:
        print(f"FAILURE (PostgreSQL): {e}")

db_uri = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{dbname}"

try:
    print("Trying with mysql-connector-python (RAW PW)...")
    ssl_args = {
        "ssl_ca": "4_frontend_app/ca.pem",
        "ssl_verify_cert": False
    }
    engine = create_engine(db_uri, pool_pre_ping=True, connect_args=ssl_args)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT 1")).scalar()
        print(f"SUCCESS (RAW PW): {res}")
except Exception as e:
    print(f"FAILURE (RAW PW): {e}")
