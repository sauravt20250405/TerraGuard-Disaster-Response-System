import os
import urllib.parse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import time

load_dotenv()

def get_engine():
    host = os.getenv("DB_HOST", "").strip()
    port = os.getenv("DB_PORT", "").strip()
    user = os.getenv("DB_USER", "").strip()
    password = os.getenv("DB_PASSWORD", "").strip()
    dbname = os.getenv("DB_NAME", "").strip()
    
    if not host:
        print("DEBUG: No remote host found. Using local SQLite.")
        db_path = "terraguard_prod.db"
        return create_engine(f"sqlite:///{db_path}")

    print(f"DEBUG: Connecting to {host}:{port} for user {user} on db {dbname}")
    
    # Try different drivers and handshakes
    protocols = [
        f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{dbname}?auth_plugin=mysql_native_password&ssl_disabled=False",
        f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{dbname}?auth_plugin=caching_sha2_password&ssl_disabled=False",
        f"mysql+pymysql://{user}:{urllib.parse.quote_plus(password)}@{host}:{port}/{dbname}"
    ]
    
    ssl_args = {"ssl_ca": "4_frontend_app/ca.pem"} if os.path.exists("4_frontend_app/ca.pem") else {}

    for uri in protocols:
        try:
            print(f"Trying {uri.split('://')[0]}...")
            engine = create_engine(uri, connect_args=ssl_args if "pymysql" not in uri else {"ssl": {"ca": "4_frontend_app/ca.pem"}}, connect_timeout=3)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                print(f"SUCCESS: Connected using {uri.split('://')[0]}")
                return engine
        except Exception as e:
            print(f"FAILURE: Remote SQL connection failed. Details: {e}")
    
    print("DEBUG: All remote options failed. Seeding LOCAL SQLite database instead.")
    db_path = "terraguard_prod.db"
    return create_engine(f"sqlite:///{db_path}")

def bootstrap():
    engine = get_engine()
    
    with engine.begin() as conn:
        print("Wiping existing tables...")
        # Use a generic approach for dropping tables (MySQL/SQLite compatible)
        tables = ["SOS_Requests", "Community_Reports", "Weather_Logs", "Digital_Vault", "Geological_Zones", "Users", "Roles"]
        
        # SQLite needs different syntax for foreign key checks
        is_sqlite = "sqlite" in str(engine.url)
        if not is_sqlite:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        
        for table in tables:
            try:
                conn.execute(text(f"DROP TABLE IF EXISTS {table};"))
            except:
                pass
        
        if not is_sqlite:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))

        print("Creating tables...")
        ai_str = "AUTOINCREMENT" if is_sqlite else "AUTO_INCREMENT"
        
        # Roles
        conn.execute(text(f'''
            CREATE TABLE Roles (
                role_id INTEGER PRIMARY KEY {ai_str},
                role_name VARCHAR(50) UNIQUE NOT NULL
            );
        '''))
        
        # Users
        conn.execute(text(f'''
            CREATE TABLE Users (
                user_id INTEGER PRIMARY KEY {ai_str},
                name VARCHAR(100) NOT NULL,
                phone_number VARCHAR(15) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role_id INTEGER,
                blood_group VARCHAR(10) DEFAULT 'Unknown',
                medical_conditions TEXT,
                emergency_contact VARCHAR(15) DEFAULT '',
                address TEXT,
                age INTEGER DEFAULT 0,
                FOREIGN KEY (role_id) REFERENCES Roles(role_id) ON DELETE SET NULL
            );
        '''))
        
        # SOS_Requests
        conn.execute(text(f'''
            CREATE TABLE SOS_Requests (
                sos_id INTEGER PRIMARY KEY {ai_str},
                user_id INTEGER,
                raw_message TEXT NOT NULL,
                latitude DECIMAL(10, 8),
                longitude DECIMAL(11, 8),
                ai_severity_score INTEGER DEFAULT 0,
                ai_category VARCHAR(50) DEFAULT 'Unclassified',
                status VARCHAR(20) DEFAULT 'Pending',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
            );
        '''))
        
        # Digital_Vault
        conn.execute(text(f'''
            CREATE TABLE Digital_Vault (
                doc_id INTEGER PRIMARY KEY {ai_str},
                user_id INTEGER,
                filename VARCHAR(255) NOT NULL,
                filepath TEXT,
                file_data MEDIUMTEXT,
                file_type VARCHAR(100) DEFAULT 'application/octet-stream',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
            );
        '''))
        
        # Seed Roles
        print("Seeding roles...")
        for role in ['Civilian', 'Medical_Response', 'Police_Dispatch', 'NDRF_Rescue']:
            conn.execute(text("INSERT INTO Roles (role_name) VALUES (:name)"), {"name": role})
        
        # Seed Demo Users
        print("Seeding demo users...")
        users = [
            ("Commander Arjun", "9988776655", "pbkdf2:sha256:260000$testhash", 4, "O+", "None", "88, Rescue HQ", 38),
            ("Officer Sarah", "9876543210", "pbkdf2:sha256:260000$testhash", 2, "A-", "Asthma", "Hospital Block B", 29),
            ("Citizen Rahul", "9123456789", "pbkdf2:sha256:260000$testhash", 1, "B+", "None", "G-14, Green Park", 24)
        ]
        for name, phone, pw, role_id, bg, mc, addr, age in users:
            conn.execute(text('''
                INSERT INTO Users (name, phone_number, password_hash, role_id, blood_group, medical_conditions, address, age)
                VALUES (:name, :phone, :pw, :role_id, :bg, :mc, :addr, :age)
            '''), {"name": name, "phone": phone, "pw": pw, "role_id": role_id, "bg": bg, "mc": mc, "addr": addr, "age": age})
        
        # Seed Demo SOS
        print("Seeding SOS requests...")
        sos_data = [
            (3, "House flooded, help!", 30.3165, 78.0322, 9, "Flood", "Pending"),
            (3, "Landslide blocked road, trapped in car", 30.3200, 78.0400, 10, "Landslide", "Pending")
        ]
        for uid, msg, lat, lon, sev, cat, stat in sos_data:
            conn.execute(text('''
                INSERT INTO SOS_Requests (user_id, raw_message, latitude, longitude, ai_severity_score, ai_category, status)
                VALUES (:uid, :msg, :lat, :lon, :sev, :cat, :stat)
            '''), {"uid": uid, "msg": msg, "lat": lat, "lon": lon, "sev": sev, "cat": cat, "stat": stat})

        print("BOOTSTRAP COMPLETE!")

if __name__ == "__main__":
    bootstrap()
