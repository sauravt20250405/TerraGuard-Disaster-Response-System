"""
TerraGuard Production API - Real-Time Disaster Response & Rescue Operations Suite
Flask REST API with RBAC, SOS triage, and geospatial incident management.
"""
import os
import urllib.parse
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import joblib
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from werkzeug.security import check_password_hash
from flask import send_from_directory
import numpy as np

# --- RESILIENT PATH RESOLUTION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
CA_CERT_PATH = os.path.join(BASE_DIR, "ca.pem")
NLP_MODEL_PATH = os.path.join(PROJECT_ROOT, "3_backend_services", "sos_nlp_model.pkl")
DISASTER_MODEL_PATH = os.path.join(PROJECT_ROOT, "3_backend_services", "disaster_risk_model.pkl")

_env_path = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(_env_path)
if not os.path.exists(_env_path):
    print(f"[WARN] .env not found at {_env_path}")

app = Flask(__name__)
CORS(app)

# --- CLOUD CONNECTION (All credentials from .env) ---
def get_engine():
    user = (os.getenv("DB_USER") or "avnadmin").strip()
    password = (os.getenv("DB_PASSWORD") or "").strip().strip("\r")
    host = (os.getenv("DB_HOST") or "terraguard-db-project-e68.a.aivencloud.com").strip()
    port = (os.getenv("DB_PORT") or "20095").strip()
    # Aiven expects initial connection to defaultdb; we USE TerraGuard_DB in each query
    db_name = "defaultdb"

    if not password:
        raise ValueError("DB_PASSWORD must be set in .env. Check that .env exists in project root.")

    safe_password = urllib.parse.quote_plus(password)
    connection_string = f"mysql+pymysql://{user}:{safe_password}@{host}:{port}/{db_name}"

    return create_engine(
        connection_string,
        connect_args={"ssl": {"ca": CA_CERT_PATH}}
    )

engine = get_engine()

# --- LOAD NLP MODEL ---
try:
    nlp_models = joblib.load(NLP_MODEL_PATH)
    print(f"[OK] NLP model loaded from {NLP_MODEL_PATH}")
except Exception as e:
    nlp_models = None
    print(f"[WARN] NLP model not found at {NLP_MODEL_PATH}: {e}")

# --- LOAD DISASTER RISK MODEL (disasterIND.csv) ---
disaster_model = None
try:
    disaster_model = joblib.load(DISASTER_MODEL_PATH)
    print(f"[OK] Disaster risk model loaded from {DISASTER_MODEL_PATH}")
except Exception as e:
    print(f"[WARN] Disaster risk model not found: {e}. Run: python 2_ai_engines/train_disaster_risk.py")

# --- Serve frontend (avoids file:// CORS issues) ---
@app.route("/")
def serve_app():
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(BASE_DIR, path)

# --- DEV MODE: bypass DB when Aiven unreachable (for UI testing) ---
DEV_MODE = os.getenv("TERRAGUARD_DEV_MODE", "").strip().lower() in ("1", "true", "yes")
if DEV_MODE:
    print("[DEV MODE] Login bypass active. Use 9876543210 or 9876543211 / test123")
DEV_INCIDENTS = []  # In-memory tickets when DB unavailable
DEV_INCIDENT_ID = 0
DEV_COMMUNITY_REPORTS = []  # In-memory community hazard reports
DEV_REPORT_ID = 0

DEMO_USERS = {
    "9876543210": {"user_id": 1, "role_id": 1, "role_name": "Civilian", "name": "Rahul Sharma", "blood_group": "O+"},
    "9876543211": {"user_id": 2, "role_id": 2, "role_name": "Medical_Response", "name": "Dr. Aditi", "blood_group": "A-"},
}
DEMO_PASSWORD = "test123"

def get_demo_user(identifier):
    """Fallback helper to generate mock user details for the agency dashboard."""
    for k, v in DEMO_USERS.items():
        if v["user_id"] == identifier or k == str(identifier):
            return {"name": v.get("name", "Unknown"), "phone": k, "blood_group": v.get("blood_group", "Unknown")}
    return {"name": "Citizen " + str(identifier), "phone": "+91-XXXXXXXXXX", "blood_group": "Unknown"}

# ==========================================
# API: LOGIN (RBAC Authentication)
# ==========================================
@app.route("/api/login", methods=["POST"])
def login():
    """Validate phone_number and password against Users table. Returns user_id, role_id, role_name."""
    data = request.json or {}
    phone_number = (data.get("phone_number") or "").strip()
    password = (data.get("password") or "").strip()

    if not phone_number or not password:
        return jsonify({"error": "phone_number and password required"}), 400

    # DEV_MODE: bypass DB with demo credentials when Aiven is unreachable
    if DEV_MODE and phone_number in DEMO_USERS and password == DEMO_PASSWORD:
        u = DEMO_USERS[phone_number]
        return jsonify({"success": True, "user_id": u["user_id"], "role_id": u["role_id"], "role_name": u["role_name"]})

    try:
        with engine.begin() as conn:
            conn.execute(text("USE TerraGuard_DB"))
            result = conn.execute(
                text("""
                    SELECT u.user_id, u.password_hash, u.role_id, r.role_name
                    FROM Users u
                    LEFT JOIN Roles r ON u.role_id = r.role_id
                    WHERE u.phone_number = :phone
                """),
                {"phone": phone_number}
            ).fetchone()

        if not result:
            return jsonify({"error": "Invalid phone number or password"}), 401

        user_id, password_hash, role_id, role_name = result
        if not check_password_hash(password_hash, password):
            return jsonify({"error": "Invalid phone number or password"}), 401

        return jsonify({
            "success": True,
            "user_id": int(user_id),
            "role_id": int(role_id) if role_id else None,
            "role_name": role_name or "Civilian"
        })
    except Exception as e:
        if DEV_MODE and phone_number in DEMO_USERS and password == DEMO_PASSWORD:
            u = DEMO_USERS[phone_number]
            return jsonify({"success": True, "user_id": u["user_id"], "role_id": u["role_id"], "role_name": u["role_name"]})
        return jsonify({"error": str(e)}), 500

# ==========================================
# API: SEND SOS (Cloud-Ready with Reported status)
# ==========================================
@app.route("/api/send_sos", methods=["POST"])
def send_sos():
    data = request.json or {}
    sos_message = (data.get("message") or "").strip()
    user_id = data.get("user_id", 1)

    if not sos_message or not nlp_models:
        return jsonify({"error": "Message empty or AI offline"}), 400

    predicted_category = nlp_models["category_model"].predict([sos_message])[0]
    predicted_severity = int(nlp_models["severity_model"].predict([sos_message])[0])

    try:
        with engine.begin() as conn:
            conn.execute(text("USE TerraGuard_DB"))
            query = text("""
                INSERT INTO SOS_Requests (user_id, raw_message, latitude, longitude, ai_severity_score, ai_category, status)
                VALUES (:uid, :msg, 31.1048, 77.1734, :sev, :cat, 'Reported')
            """)
            conn.execute(query, {
                "uid": user_id,
                "msg": sos_message,
                "sev": predicted_severity,
                "cat": predicted_category
            })
    except Exception as e:
        if DEV_MODE:
            global DEV_INCIDENT_ID
            DEV_INCIDENT_ID += 1
            ticket = {
                "sos_id": DEV_INCIDENT_ID,
                "user_id": user_id,
                "raw_message": sos_message,
                "latitude": 31.1048,
                "longitude": 77.1734,
                "ai_severity_score": predicted_severity,
                "ai_category": predicted_category,
                "status": "Reported",
            }
            DEV_INCIDENTS.append(ticket)
            return jsonify({
                "success": True,
                "category": predicted_category,
                "severity": predicted_severity
            })
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "success": True,
        "category": predicted_category,
        "severity": predicted_severity
    })

# ==========================================
# API: TRANSFER INCIDENT (Department Coordination)
# ==========================================
@app.route("/api/transfer_incident", methods=["PUT"])
def transfer_incident():
    """Transfer an active SOS incident to another department."""
    data = request.json or {}
    sos_id = data.get("sos_id")
    new_dept = data.get("department")
    
    if not sos_id or not new_dept:
        return jsonify({"error": "sos_id and department required"}), 400

    try:
        with engine.begin() as conn:
            conn.execute(text("USE TerraGuard_DB"))
            res = conn.execute(
                text("UPDATE SOS_Requests SET ai_category = :dept WHERE sos_id = :sid"),
                {"dept": new_dept, "sid": sos_id}
            )
            if res.rowcount == 0:
                return jsonify({"error": "SOS request not found"}), 404
        return jsonify({"success": True, "department": new_dept})
    except Exception as e:
        if DEV_MODE:
            for t in DEV_INCIDENTS:
                if t["sos_id"] == sos_id:
                    t["ai_category"] = new_dept
                    return jsonify({"success": True, "department": new_dept})
            return jsonify({"error": "SOS request not found"}), 404
        return jsonify({"error": str(e)}), 500

# ==========================================
# API: UPDATE STATUS (Rescue Dispatch)
# ==========================================
@app.route("/api/update_status", methods=["PUT"])
def update_status():
    """Change SOS status from 'Reported' to 'Rescue in Progress' (Dispatch Team action)."""
    data = request.json or {}
    sos_id = data.get("sos_id")
    new_status = data.get("status", "Rescue in Progress")

    if not sos_id:
        return jsonify({"error": "sos_id required"}), 400

    valid_statuses = ("Reported", "Pending", "Requires_Dispatch", "Rescue in Progress", "Resolved")
    if new_status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of: {valid_statuses}"}), 400

    try:
        with engine.begin() as conn:
            conn.execute(text("USE TerraGuard_DB"))
            result = conn.execute(
                text("UPDATE SOS_Requests SET status = :status WHERE sos_id = :sid"),
                {"status": new_status, "sid": sos_id}
            )
            if result.rowcount == 0:
                return jsonify({"error": "SOS request not found"}), 404

        return jsonify({"success": True, "sos_id": sos_id, "status": new_status})
    except Exception as e:
        if DEV_MODE:
            for t in DEV_INCIDENTS:
                if t["sos_id"] == sos_id:
                    t["status"] = new_status
                    break
            return jsonify({"success": True, "sos_id": sos_id, "status": new_status})
        return jsonify({"error": str(e)}), 500

# ==========================================
# API: GET DASHBOARD (Role-filtered + coordinates for map)
# ==========================================
@app.route("/api/get_dashboard/<role>", methods=["GET"])
def get_dashboard(role):
    """Fetch SOS tickets filtered by department, with lat/long and reporter details."""
    try:
        with engine.begin() as conn:
            conn.execute(text("USE TerraGuard_DB"))
            try:
                # Try querying with User table if it exists
                query = text("""
                    SELECT s.sos_id, s.raw_message, s.ai_severity_score, s.ai_category, s.status, s.timestamp,
                           s.latitude, s.longitude, s.user_id, u.phone_number
                    FROM SOS_Requests s
                    LEFT JOIN Users u ON s.user_id = u.user_id
                    WHERE s.ai_category = :role
                    ORDER BY s.ai_severity_score DESC
                """)
                sos_df = pd.read_sql(query, conn, params={"role": role})
            except:
                # Fallback to pure SOS_requests query if Users join fails
                query = text("""
                    SELECT sos_id, raw_message, ai_severity_score, ai_category, status, timestamp,
                           latitude, longitude, user_id
                    FROM SOS_Requests
                    WHERE ai_category = :role
                    ORDER BY s.ai_severity_score DESC
                """)
                sos_df = pd.read_sql(query, conn, params={"role": role})

            weather_query = text("SELECT rainfall_mm, ai_risk_score FROM Weather_Logs ORDER BY log_id DESC LIMIT 1")
            weather_df = pd.read_sql(weather_query, conn)

        emergencies = sos_df.to_dict(orient="records")
        for e in emergencies:
            prof = get_demo_user(e.get("phone_number") or e.get("user_id"))
            e["reporter_name"] = prof["name"]
            e["reporter_phone"] = prof["phone"]
            e["blood_group"] = prof["blood_group"]
            
        weather = weather_df.to_dict(orient="records")[0] if not weather_df.empty else None

        return jsonify({
            "emergencies": emergencies,
            "weather": weather
        })
    except Exception as e:
        if DEV_MODE:
            filtered = [t for t in DEV_INCIDENTS if t.get("ai_category") == role]
            filtered.sort(key=lambda x: x.get("ai_severity_score", 0), reverse=True)
            for e_ticket in filtered:
                prof = get_demo_user(e_ticket.get("user_id"))
                e_ticket["reporter_name"] = prof["name"]
                e_ticket["reporter_phone"] = prof["phone"]
                e_ticket["blood_group"] = prof["blood_group"]
            return jsonify({"emergencies": filtered, "weather": None})
        return jsonify({"error": str(e)}), 500

# ==========================================
# API: GET LIVE INCIDENTS (All SOS for map - optional)
# ==========================================
@app.route("/api/incidents", methods=["GET"])
def get_incidents():
    """Fetch all SOS requests with coordinates for live incident map."""
    try:
        with engine.begin() as conn:
            conn.execute(text("USE TerraGuard_DB"))
            df = pd.read_sql(
                text("""
                    SELECT sos_id, raw_message, ai_category, ai_severity_score, status,
                           latitude, longitude, timestamp, user_id
                    FROM SOS_Requests
                    ORDER BY timestamp DESC
                """),
                conn
            )
        recs = df.to_dict(orient="records")
        for r in recs:
            prof = get_demo_user(r.get("user_id"))
            r["reporter_name"] = prof["name"]
        return jsonify({"incidents": recs})
    except Exception as e:
        if DEV_MODE:
            recs = list(reversed(DEV_INCIDENTS))
            for r in recs:
                prof = get_demo_user(r.get("user_id"))
                r["reporter_name"] = prof["name"]
            return jsonify({"incidents": recs})
        return jsonify({"error": str(e)}), 500

# ==========================================
# API: DISASTER RISK BY LOCATION (disasterIND.csv)
# ==========================================
@app.route("/api/disaster_risk", methods=["GET"])
def get_disaster_risk():
    """Predict disaster risk for a location using historical India disaster data."""
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    if lat is None or lng is None:
        lat, lng = 31.1048, 77.1734  # Shimla default
    if not disaster_model:
        return jsonify({"error": "Disaster model not loaded", "risk_score": 0, "nearby": []})
    tree = disaster_model["tree"]
    df = disaster_model["df"]
    radius_km = 150  # Search within 150 km
    lat_rad = np.radians([[lat, lng]])
    indices = tree.query_radius(lat_rad, r=radius_km / 6371)[0]
    if len(indices) == 0:
        return jsonify({
            "risk_score": 0,
            "nearby": [],
            "top_disaster_types": [],
            "message": "No historical disasters in this region"
        })
    nearby = df.iloc[indices]
    type_counts = nearby["disaster_type"].value_counts()
    avg_severity = nearby["severity"].mean()
    risk_score = min(100, int(len(indices) * 5 + avg_severity * 5))
    top_types = [{"type": t, "count": int(c)} for t, c in type_counts.head(5).items()]
    records = nearby.head(10)[["Latitude", "Longitude", "disaster_type", "severity", "Location", "Start Year"]].to_dict(orient="records")
    for r in records:
        r["severity"] = int(r["severity"]) if pd.notna(r["severity"]) else 0
        r["Start Year"] = int(r["Start Year"]) if pd.notna(r["Start Year"]) else None
    return jsonify({
        "risk_score": risk_score,
        "nearby_count": len(indices),
        "top_disaster_types": top_types,
        "avg_severity": round(float(avg_severity), 1),
        "nearby": records,
    })

# ==========================================
# API: GET LATEST RISK (For map border/indicator)
# ==========================================
@app.route("/api/weather_risk", methods=["GET"])
def get_weather_risk():
    """Latest ai_risk_score for heatmap/risk indicator (red if > 80%)."""
    try:
        with engine.begin() as conn:
            conn.execute(text("USE TerraGuard_DB"))
            result = conn.execute(
                text("SELECT ai_risk_score FROM Weather_Logs ORDER BY log_id DESC LIMIT 1")
            ).fetchone()
        score = float(result[0]) if result else 0.0
        return jsonify({"ai_risk_score": score, "high_risk": score > 80})
    except Exception as e:
        return jsonify({"ai_risk_score": 0, "high_risk": False})  # Safe fallback

# ==========================================
# API: COMMUNITY REPORTING (Non-Emergency Hazards)
# ==========================================
@app.route("/api/community_report", methods=["POST"])
def community_report():
    """Allows citizens to report minor hazards (fallen trees, road blocks, etc)."""
    data = request.json or {}
    report_type = data.get("type", "General Hazard")
    description = (data.get("description") or "").strip()
    lat = data.get("lat")
    lng = data.get("lng")
    user_id = data.get("user_id", 1)

    if not description or lat is None or lng is None:
        return jsonify({"error": "Description, lat, and lng are required"}), 400

    try:
        with engine.begin() as conn:
            conn.execute(text("USE TerraGuard_DB"))
            try:
                query = text("""
                    INSERT INTO Community_Reports (user_id, report_type, description, latitude, longitude, status, verification_count)
                    VALUES (:uid, :type, :desc, :lat, :lng, 'Reported', 1)
                """)
                conn.execute(query, {
                    "uid": user_id, "type": report_type, "desc": description, "lat": lat, "lng": lng
                })
            except Exception as inner_e:
                print(f"[WARN] DB Insert failed for Community_Reports. Falling back to memory. Error: {inner_e}")
                raise inner_e # Trigger DEV_MODE fallback
                
        return jsonify({"success": True})
    except Exception as e:
        global DEV_REPORT_ID
        DEV_REPORT_ID += 1
        report = {
            "report_id": DEV_REPORT_ID,
            "user_id": user_id,
            "report_type": report_type,
            "description": description,
            "latitude": lat,
            "longitude": lng,
            "status": "Reported",
            "verification_count": 1,
            "timestamp": pd.Timestamp.now().isoformat()
        }
        DEV_COMMUNITY_REPORTS.append(report)
        return jsonify({"success": True, "fallback": True})

@app.route("/api/community_reports", methods=["GET"])
def get_community_reports():
    """Fetch all active community hazard reports for the live map."""
    try:
        with engine.begin() as conn:
            conn.execute(text("USE TerraGuard_DB"))
            query = text("""
                SELECT report_id, report_type, description, latitude, longitude, status, verification_count, timestamp
                FROM Community_Reports
                WHERE status != 'Resolved'
            """)
            df = pd.read_sql(query, conn)
        return jsonify({"reports": df.to_dict(orient="records")})
    except Exception as e:
        return jsonify({"reports": list(reversed(DEV_COMMUNITY_REPORTS))})

@app.route("/api/verify_report", methods=["POST"])
def verify_report():
    """Increment verification count for crowdsourced reports."""
    data = request.json or {}
    report_id = data.get("report_id")
    if not report_id:
        return jsonify({"error": "report_id required"}), 400

    try:
        with engine.begin() as conn:
            conn.execute(text("USE TerraGuard_DB"))
            res = conn.execute(text("UPDATE Community_Reports SET verification_count = verification_count + 1 WHERE report_id = :rid"), {"rid": report_id})
            if res.rowcount == 0:
                return jsonify({"error": "Report not found"}), 404
        return jsonify({"success": True})
    except Exception as e:
        for r in DEV_COMMUNITY_REPORTS:
            if r["report_id"] == report_id:
                r["verification_count"] += 1
                return jsonify({"success": True, "fallback": True})
        return jsonify({"error": "Report not found in memory"}), 404

if __name__ == "__main__":
    app.run(port=5000, debug=True)
