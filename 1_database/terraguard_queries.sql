-- ============================================================
-- TerraGuard Disaster Response System
-- MySQL Workbench Queries for Presentation & Data Verification
-- ============================================================

USE defaultdb;

-- 1. VIEW ALL REGISTERED USERS (Disaster-Ready Profiles)
SELECT 
    u.user_id,
    u.name AS "Full Name",
    u.phone_number AS "Phone",
    r.role_name AS "Role",
    u.blood_group AS "Blood Group",
    u.age AS "Age",
    u.emergency_contact AS "Emergency Contact",
    u.address AS "Address",
    u.medical_conditions AS "Medical Conditions"
FROM Users u
LEFT JOIN Roles r ON u.role_id = r.role_id
ORDER BY u.user_id;


-- 2. VIEW ALL ACTIVE SOS EMERGENCIES (Command Center Feed)
SELECT 
    s.sos_id AS "Ticket #",
    u.name AS "Victim Name",
    u.phone_number AS "Victim Phone",
    u.blood_group AS "Blood Group",
    s.raw_message AS "Distress Signal",
    s.ai_category AS "AI Department Routing",
    s.ai_severity_score AS "AI Severity (0-10)",
    s.status AS "Status",
    s.latitude AS "GPS Lat",
    s.longitude AS "GPS Lng",
    s.timestamp AS "Received At"
FROM SOS_Requests s
LEFT JOIN Users u ON s.user_id = u.user_id
ORDER BY s.timestamp DESC;

-- 3. VIEW ALL COMMUNITY HAZARD REPORTS
SELECT 
    report_id,
    report_type AS "Hazard Type",
    description AS "Description",
    latitude AS "GPS Lat",
    longitude AS "GPS Lng",
    status AS "Status",
    verification_count AS "Verified By",
    timestamp AS "Reported At"
FROM Community_Reports
ORDER BY timestamp DESC;

-- 4. VIEW DIGITAL VAULT DOCUMENTS (Encrypted Document Store)
SELECT
    dv.doc_id,
    u.name AS "Owner",
    dv.filename AS "Document",
    dv.file_type AS "MIME Type",
    LENGTH(dv.file_data) AS "Size (chars base64)",
    dv.timestamp AS "Uploaded At"
FROM Digital_Vault dv
LEFT JOIN Users u ON dv.user_id = u.user_id
ORDER BY dv.timestamp DESC;

-- 5. VIEW WEATHER & LANDSLIDE RISK LOGS (AI Sensor Data)
SELECT 
    log_id,
    zone_id AS "Zone",
    rainfall_mm AS "Rainfall (mm)",
    soil_moisture_percent AS "Soil Moisture %",
    ai_risk_score AS "AI Risk Score",
    timestamp AS "Logged At"
FROM Weather_Logs
ORDER BY log_id DESC
LIMIT 20;

-- 6. VIEW SYSTEM ROLES
SELECT * FROM Roles;

-- 7. DASHBOARD SUMMARY (Presentation Metrics)
SELECT 
    (SELECT COUNT(*) FROM Users) AS "Total Users",
    (SELECT COUNT(*) FROM SOS_Requests) AS "Total SOS Alerts",
    (SELECT COUNT(*) FROM SOS_Requests WHERE status = 'Reported') AS "Pending Alerts",
    (SELECT COUNT(*) FROM SOS_Requests WHERE status = 'Rescue in Progress') AS "Active Rescues",
    (SELECT COUNT(*) FROM Community_Reports) AS "Hazard Reports",
    (SELECT COUNT(*) FROM Digital_Vault) AS "Vault Documents";
