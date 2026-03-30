# TerraGuard: Real-Time Disaster Response & Rescue Operations Suite

**TerraGuard** is a comprehensive, enterprise-level AI-powered platform designed to optimize disaster response, track real-time geological risks, and streamline rescue operations. By combining live IoT-style sensor data, machine learning models, and a centralized dashboard, TerraGuard empowers emergency agencies (NDRF, Police, Medical), and civilians to collaborate effectively during critical situations.

## 🚀 Core Capabilities

### 1. AI-Powered SOS Triage (NLP Engine)
Incoming civilian SOS messages are parsed by a custom Natural Language Processing (NLP) model trained on disaster data. 
*   **Intelligent Categorization:** Automatically assigns the SOS to the relevant department (Medical_Response, Fire_Department, Police, NDRF).
*   **Severity Scoring:** Attributes a 1-10 severity score based on the urgency detected in the text, allowing responders to sort and prioritize life-threatening situations dynamically.

### 2. Landslide & Environmental Risk Engine (Virtual Sensor)
A continuous backend daemon acts as a "Virtual AI Sensor" for high-risk geological zones (e.g., Shimla Ridge, Kullu Valley).
*   **Live Data Ingestion:** Fetches real-time localized rainfall and soil moisture percentages via the Open-Meteo API.
*   **Machine Learning Predictor:** Uses a `RandomForestClassifier` trained on historical Indian mass movement data (`disasterIND.csv`) combined with synthetic slope/soil features to emit a real-time landslide risk percentage. Automatically flags regions above an 80% risk threshold.

### 3. Role-Based Access Control (RBAC) & Incident Management
Secure authentication ensuring appropriate data isolation for different responders.
*   **Custom Dashboards:** Responders log in and only see incidents categorized for their department.
*   **Department Transfers:** If an incident requires different expertise, agencies can seamlessly transfer cases across departments.
*   **Status Dispatch:** Track emergencies from "Reported" to "Rescue in Progress" to "Resolved".

### 4. Live Geospatial Incident Map
A real-time frontend visualizer plotting active SOS emergencies and weather risk models.
*   **Historical Risk Analysis:** Calculates geographical risk metrics within a 150km radius using a K-D Tree approach against historical disaster data.
*   **Community Hazards (Crowdsourcing):** Allows civilians to report non-life-threatening infrastructure damage (e.g., collapsed bridges, fallen trees), featuring a multi-user "verification" counter to confirm severity.

## 📂 Project Architecture

```
TerraGuard/
├── 1_database/               # Cloud SQL deployment scripts 
│   ├── setup_schema.sql      # Core schema (Users, Roles, SOS_Requests, Weather_Logs)
│   └── seed_test_user.py     # Initial mock user seeding
├── 2_ai_engines/             # Machine Learning Training Pipelines
│   ├── train_landslide_ml.py # Random Forest logic for Geological predictive models
│   ├── train_sos_nlp.py      # NLP Vectorization & Classification models
│   └── train_disaster_risk.py# Distance-based historical risk mapping
├── 3_backend_services/       # Cron/Daemon workers
│   └── virtual_sensor.py     # Live API polling & AI Model inferencing
└── 4_frontend_app/           # Core API and UI
    ├── api.py                # Flask REST API endpoints
    └── index.html            # Core centralized frontend
```

## 🔌 API Endpoints Reference

The `api.py` Flask app exposes the following primary REST endpoints:

**Authentication & Roles:**
*   `POST /api/login`: Validates PBKDF2 hashed credentials and returns `user_id`, `role_id`, and `role_name`.

**Emergency (SOS) Engine:**
*   `POST /api/send_sos`: Ingests civilian messages, triggers NLP AI models, updates the cloud SQL DB dynamically.
*   `PUT /api/transfer_incident`: Inter-departmental ticket transfers.
*   `PUT /api/update_status`: State management for dispatch vehicles (e.g., "Pending" -> "Resolved").

**Dashboard & Map:**
*   `GET /api/get_dashboard/<role>`: Fetches role-isolated incidents joined with user demographics (e.g., Blood Group, Reporter Phone).
*   `GET /api/incidents`: Fetch all global active points for the map view.
*   `GET /api/disaster_risk`: Predicts aggregate hazard risks utilizing historical data mapped against user GPS coordinates.

**Community Reports:**
*   `POST /api/community_report`: Post non-emergency geological or structural hazards.
*   `GET /api/community_reports`: Fetch active hazard lists.
*   `POST /api/verify_report`: Upvote civic hazards to prove legitimacy.

## 🛠️ Setup and Installation

### 1. Requirements

*   Python 3.8+
*   MySQL 8.0+ (Tested extensively with Aiven Cloud DBs)
*   Required Python modules: `Flask`, `Flask-cors`, `SQLAlchemy`, `PyMySQL`, `Scikit-Learn`, `Pandas`, `Joblib`.

### 2. Environment Configuration

Install dependencies:
```bash
pip install -r requirements.txt
```

Create a `.env` file containing your database keys:
```env
DB_USER=avnadmin
DB_PASSWORD=your_secure_password
DB_HOST=terraguard-db-project-e68.a.aivencloud.com
DB_PORT=20095
```
*(Place your `ca.pem` certificate in both `3_backend_services` and `4_frontend_app` to enable SSL database connections).*

### 3. Database Initialization
Run the provided `setup_schema.sql` against your target database to mount tables, roles, and dummy geographical configurations.

### 4. Model Training (Optional)
If you wish to update the AI logic, execute the pipelines in `2_ai_engines/` directly:
```bash
python 2_ai_engines/train_landslide_ml.py
python 2_ai_engines/train_sos_nlp.py
```
*(This produces `.pkl` model assets dynamically).*

### 5. Running the Application Suite

Because TerraGuard spans both user interfaces and background processing, you must run both primary systems:

**A. Start the Virtual Sensor Daemon (Background Task):**
```bash
cd 3_backend_services
python virtual_sensor.py
```
*You will see the terminal logging live rain metrics and AI risk analysis every 10 seconds.*

**B. Start the Central Web Server:**
```bash
cd 4_frontend_app
python api.py
```
*The web interface is now actively serving data locally at `http://127.0.0.1:5000/`.*

## 🛡️ Best Practices & Production Warning
TerraGuard utilizes synthetic and predictive data combinations (`disasterIND.csv`). It is engineered as a prototype for emergency command center integrations. Do not rely entirely on the ML output for live civic evacuation orders without multi-tier verification setups.
