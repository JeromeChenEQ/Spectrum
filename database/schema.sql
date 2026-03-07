CREATE DATABASE IF NOT EXISTS spectrum_senioraid;
USE spectrum_senioraid;

CREATE TABLE IF NOT EXISTS boxes (
    box_id INT AUTO_INCREMENT PRIMARY KEY,
    resident_name VARCHAR(120) NOT NULL,
    address VARCHAR(255) NOT NULL,
    contact_number VARCHAR(30) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    box_id INT NOT NULL,
    detected_language VARCHAR(40) NOT NULL,
    transcript TEXT NOT NULL,
    english_translation TEXT NOT NULL,
    severity ENUM('EMERGENCY', 'URGENT', 'ROUTINE') NOT NULL,
    status ENUM('open', 'acknowledged') NOT NULL DEFAULT 'open',
    is_simulated_ai BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP NULL,
    CONSTRAINT fk_alerts_boxes FOREIGN KEY (box_id) REFERENCES boxes (box_id)
);