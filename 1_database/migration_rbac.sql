-- Migration: Production RBAC & Status Values
-- Run this after setup_schema.sql to support Fire_Department and new status flow

USE TerraGuard_DB;

-- Add Fire_Department role if not exists
INSERT IGNORE INTO Roles (role_name) VALUES ('Fire_Department');

-- Ensure status column accepts new values (VARCHAR(30) for 'Rescue in Progress')
ALTER TABLE SOS_Requests MODIFY COLUMN status VARCHAR(30) DEFAULT 'Reported';

-- Optional: Create a test user with hashed password (run from Python for correct hash)
-- Password 'test123' hashed with werkzeug: from werkzeug.security import generate_password_hash; print(generate_password_hash('test123'))
-- INSERT INTO Users (name, phone_number, password_hash, role_id) VALUES
-- ('Test Civilian', '9876543210', '<hash>', 1),
-- ('Test Agency', '9876543211', '<hash>', 2);
