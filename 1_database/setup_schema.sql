-- Create and use the dedicated database
CREATE DATABASE IF NOT EXISTS TerraGuard_DB;

USE TerraGuard_DB;

-- ==========================================
-- 1. ROLE-BASED ACCESS CONTROL (RBAC)
-- ==========================================

CREATE TABLE Roles (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL
);

-- Insert the default emergency and civilian roles
INSERT INTO Roles (role_name) VALUES 
('Civilian'), 
('Medical_Response'), 
('Police_Dispatch'), 
('NDRF_Rescue');

CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(15) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL, -- Always prep for hashed passwords!
    role_id INT,
    FOREIGN KEY (role_id) REFERENCES Roles(role_id) ON DELETE SET NULL
);

-- ==========================================
-- 2. ENVIRONMENTAL TRACKING (The Landslide Predictor)
-- ==========================================

CREATE TABLE Geological_Zones (
    zone_id INT AUTO_INCREMENT PRIMARY KEY,
    zone_name VARCHAR(100) NOT NULL,
    slope_angle FLOAT, -- Steepness of the hill
    soil_type VARCHAR(50)
);

-- Insert some default high-risk dummy zones
INSERT INTO Geological_Zones (zone_name, slope_angle, soil_type) VALUES 
('Shimla Ridge', 45.5, 'Clay'), 
('Kullu Valley', 30.2, 'Loam'), 
('Dharamshala Slopes', 55.0, 'Silt');

CREATE TABLE Weather_Logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    zone_id INT,
    rainfall_mm FLOAT,
    soil_moisture_percent FLOAT,
    ai_risk_score FLOAT DEFAULT 0.0, -- Your Python script will update this
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (zone_id) REFERENCES Geological_Zones(zone_id) ON DELETE CASCADE
);

-- ==========================================
-- 3. THE Triage Engine (SOS System)
-- ==========================================

CREATE TABLE SOS_Requests (
    sos_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    raw_message TEXT NOT NULL,
    latitude DECIMAL(10, 8), -- High precision GPS coordinates
    longitude DECIMAL(11, 8),
    ai_severity_score INT DEFAULT 0, -- 1 to 10 scale
    ai_category VARCHAR(50) DEFAULT 'Unclassified', -- Medical, Fire, Security
    status VARCHAR(20) DEFAULT 'Pending', -- Pending, Dispatched, Resolved
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);