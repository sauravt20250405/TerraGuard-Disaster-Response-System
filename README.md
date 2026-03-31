# TerraGuard: Real-Time Disaster Response & Rescue Operations Suite

**Live Deployment:** [https://terraguard-disaster-response-system.onrender.com/](https://terraguard-disaster-response-system.onrender.com/)

**TerraGuard** is a comprehensive, enterprise-level AI-powered platform designed to optimize disaster response, track real-time geological risks, and streamline rescue operations. By combining live IoT-style sensor data, machine learning models, and a centralized dashboard, TerraGuard empowers emergency agencies (NDRF, Police, Medical), and civilians to collaborate effectively during critical situations.

## 🚀 Core Capabilities

### 1. AI-Powered SOS Triage (NLP Engine)
Incoming civilian SOS messages are parsed by a custom Natural Language Processing (NLP) model trained on disaster data. 
*   **Intelligent Categorization:** Automatically assigns the SOS to the relevant department (Medical_Response, Fire_Department, Police, NDRF).
*   **Severity Scoring:** Attributes a 1-10 severity score based on the urgency detected in the text, allowing responders to sort and prioritize life-threatening situations dynamically.
*   **Live GPS Tagging:** Every SOS pulse transmits the victim's exact latitude/longitude for immediate tracking.

### 2. Disaster-Ready User Profiles (New)
Civilians can maintain a mission-critical emergency profile that is **instantly shared with responders** during an SOS:
*   🩸 **Blood Group & Age**
*   ⚕️ **Medical Conditions & Allergies** (Diabetic, Asthmatic, etc.)
*   📞 **Emergency Contacts** for next-of-kin notification.
*   🏠 **Last Known Address** for search and rescue boundary setting.

### 3. Secure Digital Vault (Cloud Persistence)
A secure storage system for critical documents (ID cards, Medical records) that survives disasters:
*   **Database Persistence:** Files are stored as **Base64 strings** directly in the MySQL database, ensuring they are never lost even if server disks are wiped.
*   **Secure Access:** Viewed only by the user or assigned rescue officers during an active emergency.

### 4. Landslide & Environmental Risk Engine (Virtual Sensor)
A continuous backend daemon acts as a "Virtual AI Sensor" for high-risk geological zones:
*   **Live Data Ingestion:** Fetches real-time localized rainfall and soil moisture percentages via the Open-Meteo API.
*   **Machine Learning Predictor:** Uses a `RandomForestClassifier` trained on historical data to emit a real-time landslide risk percentage.

### 5. Live Geospatial Incident Map
A real-time frontend visualizer plotting active SOS emergencies and weather risk models.
*   **Local Resources:** Dynamically fetches nearby hospitals, police stations, and clinics within 10km using the Overpass API.
*   **Community Hazards:** Civilians report non-life-threatening infrastructure damage (fallen trees, road blocks) with multi-user verification.

## 📂 Project Architecture

```
TerraGuard/
├── 1_database/               # Cloud SQL / Workbench scripts 
│   ├── terraguard_queries.sql# Professional Query Suite for Workbench
│   └── setup_schema.sql      # Core schema (Users, Roles, SOS, Vault)
├── 2_ai_engines/             # Machine Learning Training Pipelines
│   ├── train_landslide_ml.py # Random Forest predictive models
│   ├── train_sos_nlp.py      # NLP Classification models
│   └── train_disaster_risk.py# Historical risk mapping
├── 3_backend_services/       # Cron/Daemon workers
│   └── virtual_sensor.py     # Live API polling & AI Model inferencing
└── 4_frontend_app/           # Core API and UI
    ├── api.py                # Flask REST API endpoints
    └── index.html            # Core centralized frontend
```

## 🔌 API Endpoints Reference

**Authentication & Profiles:**
*   `POST /api/login`: Secure credential validation.
*   `GET /api/profile/<id>` / `PUT /api/profile/<id>`: Manage disaster-ready medical data.

**Emergency (SOS) Engine:**
*   `POST /api/send_sos`: Ingests messages + GPS, triggers AI triage.
*   `GET /api/vault/upload` / `GET /api/vault/download/<id>`: Manage persistent base64 documents.

**Dashboard & Map:**
*   `GET /api/get_dashboard/<role>`: Role-isolated tactical feed with victim medical profiles.
*   `GET /api/disaster_risk`: Predicts aggregate hazard risks utilizing historical data.

## 🛠️ Setup and Installation

### 1. Requirements
*   Python 3.8+
*   MySQL 8.0+ (Tested extensively with **Aiven Cloud MySQL**)
*   Required modules: `Flask`, `sqlalchemy`, `pymysql`, `pandas`, `joblib`, `scikit-learn`.

### 2. Environment Configuration
Create a `.env` file:
```env
DB_USER=avnadmin
DB_PASSWORD=your_aiven_password
DB_HOST=mysql-xxxx-project-xxxx.aivencloud.com
DB_PORT=20095
DB_NAME=defaultdb
```
*(Place your `ca.pem` certificate in `4_frontend_app/` to enable SSL).*

### 3. Running the Suite
1.  **Initialize Database**: Run the script in `1_database/setup_schema.sql` (or use the Workbench query suite).
2.  **Start Backend Sensor**: `python 3_backend_services/virtual_sensor.py`
3.  **Start Main App**: `python 4_frontend_app/api.py`

## 🛡️ Best Practices
TerraGuard is engineered as a prototype for emergency command center integrations. Do not rely entirely on the ML output for live civic evacuation orders without multi-tier verification.
