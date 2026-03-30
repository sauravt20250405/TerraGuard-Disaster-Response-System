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

user = (os.getenv("DB_USER") or "avnadmin").strip()
password = (os.getenv("DB_PASSWORD") or "").strip().strip("\r")
host = (os.getenv("DB_HOST") or "terraguard-db-project-e68.a.aivencloud.com").strip()
port = (os.getenv("DB_PORT") or "20095").strip()
db_name = (os.getenv("DB_NAME") or "defaultdb").strip()

# 2. Double-check for special characters by encoding them properly
# This is the industry-standard way to handle chaotic passwords
safe_password = urllib.parse.quote_plus(password)

# 3. Construct the connection string
# Note: Aiven usually requires the 'defaultdb' name if you haven't changed it
connection_string = f"mysql+pymysql://{user}:{safe_password}@{host}:{port}/{db_name}"

CA_CERT_PATH = os.path.join(BASE_DIR, "ca.pem")


# 4. Create engine with SSL requirements
engine = create_engine(
    connection_string,
    connect_args = {
    "ssl": {
        "ca": CA_CERT_PATH 
        }
    }
)


# 4. INITIALIZATION: Create your project tables on the Cloud
print("Checking Cloud Database Integrity...")
try:
    if not DEV_MODE:
        with engine.begin() as conn:
            # Create the specific database for your project
            conn.execute(text("CREATE DATABASE IF NOT EXISTS TerraGuard_DB"))
            conn.execute(text("USE TerraGuard_DB"))
            
            # Create the Weather_Logs table if it doesn't exist on Aiven yet
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS Weather_Logs (
                    log_id INT AUTO_INCREMENT PRIMARY KEY,
                    zone_id INT,
                    rainfall_mm FLOAT,
                    soil_moisture_percent FLOAT,
                    ai_risk_score FLOAT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
        print("Cloud Database Ready!")
    else:
        print("DEV MODE Active: Bypassing Cloud DB setup.")
except Exception as e:
    print(f"Connection Failed: {e}")
    if not DEV_MODE:
        exit()


if not DEV_MODE:
    print(f"Connecting to Cloud DB at {host}...")

# 2. Load the AI Brain
# 2. Load the AI Brain (Dynamically find the path)
MODEL_PATH = os.path.join(BASE_DIR, 'landslide_model.pkl')

try:
    landslide_model = joblib.load(MODEL_PATH) # Using the absolute path
    print("AI Brain loaded successfully.")
except FileNotFoundError:
    print(f"ERROR: landslide_model.pkl not found at {MODEL_PATH}")
    exit()

# 3. Target Geological Zone (Shimla Ridge)
LATITUDE = 31.1048
LONGITUDE = 77.1734
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
        risk_score = round(risk_probabilities[1] * 100, 2) 
        
        print(f"[LIVE] Shimla Ridge -> Rain: {rain}mm | Soil: {soil:.1f}% | AI Risk Score: {risk_score}%")
        
        if not DEV_MODE:
            try:
                # Insert into MySQL
                with engine.begin() as conn:
                    query = text("""
                        INSERT INTO TerraGuard_DB.Weather_Logs (zone_id, rainfall_mm, soil_moisture_percent, ai_risk_score)
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