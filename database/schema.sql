CREATE TYPE severity_enum AS ENUM ('EMERGENCY', 'URGENT', 'ROUTINE');
CREATE TYPE alert_status_enum AS ENUM ('open', 'acknowledged');

CREATE TABLE IF NOT EXISTS boxes (
    box_id SERIAL PRIMARY KEY,
    resident_name VARCHAR(120) NOT NULL,
    address VARCHAR(255) NOT NULL,
    contact_number VARCHAR(30) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id SERIAL PRIMARY KEY,
    box_id INT NOT NULL,
    detected_language VARCHAR(40) NOT NULL,
    transcript TEXT NOT NULL,
    english_translation TEXT NOT NULL,
    severity severity_enum NOT NULL,
    status alert_status_enum NOT NULL DEFAULT 'open',
    is_simulated_ai BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    acknowledged_at TIMESTAMP NULL,
    CONSTRAINT fk_alerts_boxes FOREIGN KEY (box_id) REFERENCES boxes (box_id)
);