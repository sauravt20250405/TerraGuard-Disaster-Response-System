import os
path = r"c:\Users\SAURAV THAKUR\Desktop\TerraGuard\3_backend_services\virtual_sensor.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

import re
# Replace the old connection snippet with the new SQLite snippet
pattern = r"user = \(os\.getenv\(\"DB_USER\"\).*?print\(\"Cloud Database Ready!\"\)"
replacement = """# Local SQLite Engine for Production Offline Mode
db_path = os.path.join(PROJECT_ROOT, "terraguard_prod.db")
engine = create_engine(f"sqlite:///{db_path}")

try:
    if not DEV_MODE:
        with engine.begin() as conn:
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS Weather_Logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    zone_id INTEGER,
                    rainfall_mm FLOAT,
                    soil_moisture_percent FLOAT,
                    ai_risk_score FLOAT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            '''))
        print("Database Ready!")"""

text = re.sub(pattern, replacement, text, flags=re.DOTALL)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
