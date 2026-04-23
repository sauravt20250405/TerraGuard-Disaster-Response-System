import os
import joblib
import requests
import pandas as pd
import time
import urllib.parse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
_env_path = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(_env_path)

DEV_MODE = os.getenv("TERRAGUARD_DEV_MODE", "").strip().lower() in ("1", "true", "yes")

# --- CLOUD DB CONNECTION ---
host = os.getenv("DB_HOST", "").strip()
port = os.getenv("DB_PORT", "").strip()
user = os.getenv("DB_USER", "").strip()
raw_pw = os.getenv("DB_PASSWORD", "").strip()
dbname = os.getenv("DB_NAME", "terraguard_db").strip()

engine = None
db_uri = None

if host:
    # Check for Supabase/PostgreSQL
    if "supabase" in host or port == "5432":
        db_uri = f"postgresql+psycopg2://{user}:{urllib.parse.quote_plus(raw_pw)}@{host}:{port}/{dbname}"
        try:
            print(f"Sensor: Trying PostgreSQL (Supabase)...")
            engine = create_engine(db_uri, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Sensor: SUCCESS - Connected to PostgreSQL")
        except Exception as e:
            print(f"Sensor: PostgreSQL connection failed: {e}")
            engine = None

    if engine is None:
        # Fallback to MySQL
        db_uri = f"mysql+mysqlconnector://{user}:{raw_pw}@{host}:{port}/{dbname}"
        ssl_args = {
            "ssl_ca": os.path.join(BASE_DIR, "..", "4_frontend_app", "ca.pem"),
            "ssl_verify_cert": False,
            "auth_plugin": "caching_sha2_password"
        }
        try:
            engine = create_engine(db_uri, pool_pre_ping=True, connect_args=ssl_args)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Sensor: SUCCESS - Connected to MySQL")
        except Exception as e:
            print(f"Sensor: Remote DB connection failed. Falling back to local SQLite: {e}")
            engine = None

if engine is None:
    db_path = os.path.join(PROJECT_ROOT, "terraguard_prod.db")
    db_uri = f"sqlite:///{db_path}"
    engine = create_engine(db_uri, pool_pre_ping=True)

url_str = str(engine.url)
is_sqlite = "sqlite" in url_str
is_postgres = "postgresql" in url_str

if is_sqlite:
    ai_str = "INTEGER PRIMARY KEY AUTOINCREMENT"
elif is_postgres:
    ai_str = "SERIAL PRIMARY KEY"
else:
    ai_str = "INTEGER PRIMARY KEY AUTO_INCREMENT"

ts_type = "TIMESTAMP" if is_postgres else "DATETIME"

try:
    if not DEV_MODE:
        with engine.begin() as conn:
            conn.execute(text(f'''
                CREATE TABLE IF NOT EXISTS Weather_Logs (
                    log_id {ai_str},
                    zone_id INTEGER,
                    rainfall_mm FLOAT,
                    soil_moisture_percent FLOAT,
                    ai_risk_score FLOAT,
                    timestamp {ts_type} DEFAULT CURRENT_TIMESTAMP
                )
            '''))
        print("Database Ready!")
    else:
        print("DEV MODE Active: Bypassing Cloud DB setup.")
except Exception as e:
    print(f"Connection Failed: {e}")
    print("Falling back to local SQLite to prevent deployment crash.")


if not DEV_MODE:
    print(f"Connecting to Local Production DB...")

# 2. Load the AI Brain
# 2. Load the AI Brain (Dynamically find the path)
MODEL_PATH = os.path.join(BASE_DIR, 'landslide_model.pkl')

try:
    landslide_model = joblib.load(MODEL_PATH) # Using the absolute path
    print("AI Brain loaded successfully.")
except FileNotFoundError:
    print(f"ERROR: landslide_model.pkl not found at {MODEL_PATH}")
    exit()

# 3. Target Geological Zone (Dynamic IP)
try:
    print("Fetching sensor location via IP lookup...")
    ip_resp = requests.get("https://ipapi.co/json/", timeout=5)
    ip_data = ip_resp.json()
    LATITUDE = float(ip_data.get('latitude', 31.1048))
    LONGITUDE = float(ip_data.get('longitude', 77.1734))
    CITY = ip_data.get('city', 'Unknown District')
    print(f"Virtual Sensor deployed to: {CITY} ({LATITUDE}, {LONGITUDE})")
except Exception:
    print("Could not fetch IP location, falling back to Shimla Ridge.")
    LATITUDE = 31.1048
    LONGITUDE = 77.1734
    CITY = "Unknown District"

ZONE_ID = 1 
STATIC_SLOPE = 45.5 

def fetch_live_weather():
    """Pulls live rain and soil data from the Open-Meteo API safely"""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&current=precipitation,soil_moisture_0_to_7cm"
    try:
        response = requests.get(url)
        data = response.json()
        
        # Safely extract rainfall (default to 0.0 if missing)
        rain_mm = data['current'].get('precipitation', 0.0)
        if rain_mm is None: rain_mm = 0.0
        
        # Safely extract soil moisture (default to 0.5 if missing)
        soil_raw = data['current'].get('soil_moisture_0_to_7cm', 0.5)
        if soil_raw is None: soil_raw = 0.5
            
        soil_moisture_pct = soil_raw * 100 
        
        return rain_mm, soil_moisture_pct
    except Exception as e:
        print(f"API Error: {e}")
        return 0.0, 50.0 

print(f"Virtual Sensor ACTIVE. Monitoring coordinates ({LATITUDE}, {LONGITUDE})...")
print("Press Ctrl+C to stop.")

# 4. The Continuous Monitoring Loop
try:
    while True:
        # Fetch live data
        rain, soil = fetch_live_weather()
        
        # Prepare the data for the AI Model
        ai_input = pd.DataFrame({
            'rainfall_mm': [rain],
            'soil_moisture_percent': [soil],
            'slope_angle': [STATIC_SLOPE]
        })
        
        # Ask the AI
        risk_probabilities = landslide_model.predict_proba(ai_input)[0]
        risk_score = float(round(risk_probabilities[1] * 100, 2))
        
        print(f"[LIVE] Live Zone -> Rain: {rain}mm | Soil: {soil:.1f}% | AI Risk Score: {risk_score}%")
        
        if not DEV_MODE:
            try:
                # Insert into MySQL
                with engine.begin() as conn:
                    query = text("""
                        INSERT INTO Weather_Logs (zone_id, rainfall_mm, soil_moisture_percent, ai_risk_score)
                        VALUES (:zone, :rain, :soil, :risk)
                    """)
                    conn.execute(query, {"zone": ZONE_ID, "rain": rain, "soil": soil, "risk": risk_score})
            except Exception as e:
                print(f"DB Insert Error: {e}")
        else:
            print("[DEV MODE] Bypassed database insert.")
            
        time.sleep(10)

except KeyboardInterrupt:
    print("\nVirtual Sensor safely shut down.")