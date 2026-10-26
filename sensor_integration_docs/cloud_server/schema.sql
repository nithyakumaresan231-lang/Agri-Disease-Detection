-- POLY HOUSE MySQL schema
-- Run this ONCE:
--   "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS polyhouse CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE polyhouse;

-- Every sensor-data upload from the device is stored here (full JSON payload).
CREATE TABLE IF NOT EXISTS device_data (
  id INT AUTO_INCREMENT PRIMARY KEY,
  device_id VARCHAR(64) DEFAULT '',
  customer_id VARCHAR(64) DEFAULT '',
  ts VARCHAR(64) DEFAULT '',
  payload JSON NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Every command-response (ACK) from the device is stored here.
CREATE TABLE IF NOT EXISTS commands_log (
  id INT AUTO_INCREMENT PRIMARY KEY,
  device_id VARCHAR(64) DEFAULT '',
  ts VARCHAR(64) DEFAULT '',
  payload JSON NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
