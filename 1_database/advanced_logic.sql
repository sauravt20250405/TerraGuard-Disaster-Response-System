USE TerraGuard_DB;

-- ==========================================
-- TRIGGER 1: Automated Landslide Warnings
-- ==========================================
-- When your Python Virtual Sensor inserts a new weather log, this trigger
-- checks if the AI risk score is dangerously high. If it is, the database
-- automatically generates a system-level SOS alert.

DELIMITER //
CREATE TRIGGER Landslide_Warning_Trigger
AFTER INSERT ON Weather_Logs
FOR EACH ROW
BEGIN
    IF NEW.ai_risk_score >= 80.0 THEN
        -- user_id 1 will represent the Automated System in our app
        INSERT INTO SOS_Requests (user_id, raw_message, ai_severity_score, ai_category, status)
        VALUES (
            1, 
            CONCAT('SYSTEM ALERT: Severe Landslide Risk Detected in Zone ID ', NEW.zone_id, '! Rainfall at ', NEW.rainfall_mm, 'mm.'), 
            10, 
            'Natural_Disaster', 
            'Requires_Dispatch'
        );
    END IF;
END //
DELIMITER ;


-- ==========================================
-- TRIGGER 2: Instant SOS Triage
-- ==========================================
-- When a civilian sends an SOS from their phone, Python calculates the severity.
-- Before the row is even saved, this trigger intercepts it. If the severity 
-- is critically high (8 or above), it bypasses the "Pending" queue entirely.

DELIMITER //
CREATE TRIGGER SOS_Triage_Trigger
BEFORE INSERT ON SOS_Requests
FOR EACH ROW
BEGIN
    IF NEW.ai_severity_score >= 8 THEN
        SET NEW.status = 'Requires_Dispatch';
    ELSEIF NEW.status IS NULL THEN
        SET NEW.status = 'Pending';
    END IF;
END //
DELIMITER ;