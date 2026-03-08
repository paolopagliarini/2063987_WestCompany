-- =====================================================
-- AUTOMATION RULES
-- =====================================================

CREATE TABLE automation_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    sensor_id VARCHAR(100) NOT NULL,
    operator VARCHAR(10) NOT NULL,
    threshold_value DECIMAL(10, 2) NOT NULL,
    threshold_unit VARCHAR(20),
    actuator_id VARCHAR(100) NOT NULL,
    actuator_action VARCHAR(20) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_operator CHECK (operator IN ('<', '<=', '=', '>', '>='))
);

-- =====================================================
-- OPTIONAL: Sensor readings history (useful for analytics)
-- =====================================================

CREATE TABLE sensor_readings (
    id BIGSERIAL PRIMARY KEY,
    sensor_id VARCHAR(100) NOT NULL,
    value DECIMAL(10, 4) NOT NULL,
    unit VARCHAR(20),
    source VARCHAR(50),
    recorded_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- OPTIONAL: Actuator commands history (audit trail)
-- =====================================================

CREATE TABLE actuator_commands (
    id BIGSERIAL PRIMARY KEY,
    actuator_id VARCHAR(100) NOT NULL,
    previous_state VARCHAR(20),
    new_state VARCHAR(20) NOT NULL,
    source VARCHAR(50),
    reason TEXT,
    rule_id INTEGER REFERENCES automation_rules(id) ON DELETE SET NULL,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- INDEXES
-- =====================================================

CREATE INDEX idx_sensor_readings_sensor_id ON sensor_readings(sensor_id);
CREATE INDEX idx_sensor_readings_recorded_at ON sensor_readings(recorded_at);
CREATE INDEX idx_automation_rules_active ON automation_rules(is_active);
CREATE INDEX idx_automation_rules_sensor_id ON automation_rules(sensor_id);

-- =====================================================
-- SEED DATA - Sample automation rules
-- =====================================================
-- Utili per testare all'inizio
-- INSERT INTO automation_rules (name, description, sensor_id, operator, threshold_value, threshold_unit, actuator_id, actuator_action) VALUES
--     ('Temperature High', 'Activate cooling if temp > 28C', 'greenhouse_temperature', '>', 28, 'C', 'cooling_fan', 'ON'),
--     ('Temperature Low', 'Deactivate cooling if temp < 25C', 'greenhouse_temperature', '<', 25, 'C', 'cooling_fan', 'OFF'),
--     ('CO2 High', 'Open valve if CO2 > 1000 ppm', 'habitat_co2', '>', 1000, 'ppm', 'air_valve', 'OPEN'),
--     ('Oxygen Low', 'Trigger alarm if O2 < 19.5%%', 'habitat_oxygen', '<', 19.5, '%', 'emergency_alarm', 'ON'),
--     ('Humidity Low', 'Activate pump if humidity < 40%%', 'greenhouse_humidity', '<', 40, '%', 'water_pump', 'ON');