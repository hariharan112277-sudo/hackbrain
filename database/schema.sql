-- IOB Industrial Operating Brain - Physical Storage Schema Architecture
-- Target Environment: PostgreSQL 14+ / TimescaleDB Compatible

CREATE SCHEMA IF NOT EXISTS industrial;
SET search_path TO industrial, public;

-- Custom Domains & Shared Enumerations
CREATE TYPE operational_status AS ENUM ('ONLINE', 'OFFLINE', 'MAINTENANCE', 'DECOMMISSIONED');
CREATE TYPE alarm_severity AS ENUM ('INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
CREATE TYPE alarm_state AS ENUM ('ACTIVE', 'ACKNOWLEDGED', 'CLEARED');

-- Structural Hierarchy Master Elements
CREATE TABLE plants (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    location VARCHAR(200) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (now() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (now() AT TIME ZONE 'UTC'),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE TABLE production_lines (
    id UUID PRIMARY KEY,
    plant_id UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    sequence_number INT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (now() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (now() AT TIME ZONE 'UTC'),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_plant_line_name UNIQUE (plant_id, name)
);
CREATE TABLE gateways (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    ip_address VARCHAR(45) NOT NULL,
    mac_address VARCHAR(17) NOT NULL UNIQUE,
    firmware_version VARCHAR(50) NOT NULL,
    protocol VARCHAR(20) NOT NULL DEFAULT 'MQTT',
    status operational_status NOT NULL DEFAULT 'ONLINE',
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (now() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (now() AT TIME ZONE 'UTC')
);
CREATE TABLE assets (
    id UUID PRIMARY KEY,
    production_line_id UUID NOT NULL REFERENCES production_lines(id),
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    manufacturer VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    serial_number VARCHAR(100) NOT NULL UNIQUE,
    criticality VARCHAR(20) NOT NULL,
    installation_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    commission_date TIMESTAMP WITHOUT TIME ZONE,
    status operational_status NOT NULL DEFAULT 'ONLINE',
    metadata_fields JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (now() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (now() AT TIME ZONE 'UTC'),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE TABLE machines (
    id UUID PRIMARY KEY,
    asset_id UUID NOT NULL UNIQUE REFERENCES assets(id),
    gateway_id UUID NOT NULL REFERENCES gateways(id),
    firmware_version VARCHAR(50) NOT NULL,
    operating_hours REAL NOT NULL DEFAULT 0.0,
    runtime_counter REAL NOT NULL DEFAULT 0.0,
    current_mode VARCHAR(30) NOT NULL DEFAULT 'AUTOMATIC',
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (now() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (now() AT TIME ZONE 'UTC'),
    CONSTRAINT chk_operating_hours_positive CHECK (operating_hours >= 0)
);
CREATE TABLE sensors (
    id UUID PRIMARY KEY,
    machine_id UUID NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    sensor_type VARCHAR(50) NOT NULL,
    measurement_unit VARCHAR(20) NOT NULL,
    sampling_rate_hz REAL NOT NULL,
    calibration_offset REAL NOT NULL DEFAULT 0.0,
    lower_threshold REAL,
    upper_threshold REAL,
    status operational_status NOT NULL DEFAULT 'ONLINE',
    metadata_fields JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (now() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (now() AT TIME ZONE 'UTC'),
    CONSTRAINT uq_machine_sensor_name UNIQUE (machine_id, name)
);
-- Core Telemetry Model Optimized for Time-Series Window Aggregations
CREATE TABLE telemetry (
    id UUID NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    machine_id UUID NOT NULL REFERENCES machines(id),
    sensor_id UUID NOT NULL REFERENCES sensors(id),
    measured_value DOUBLE PRECISION NOT NULL,
    quality_code INT NOT NULL DEFAULT 192,
    alarm_status VARCHAR(20) NOT NULL DEFAULT 'NORMAL',
    sequence_number INT NOT NULL,
    metadata_fields JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (id, timestamp)
) PARTITION BY RANGE (timestamp);
-- System Alerts and Event Registries
CREATE TABLE alarms (
    id UUID PRIMARY KEY,
    machine_id UUID NOT NULL REFERENCES machines(id),
    sensor_id UUID NOT NULL REFERENCES sensors(id),
    severity alarm_severity NOT NULL,
    state alarm_state NOT NULL DEFAULT 'ACTIVE',
    trigger_timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    ack_timestamp TIMESTAMP WITHOUT TIME ZONE,
    clear_timestamp TIMESTAMP WITHOUT TIME ZONE,
    trigger_value DOUBLE PRECISION NOT NULL,
    threshold_violated VARCHAR(50) NOT NULL,
    operator_notes TEXT
);
CREATE TABLE machine_events (
    id UUID PRIMARY KEY,
    machine_id UUID NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (now() AT TIME ZONE 'UTC'),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    operator_id UUID
);
CREATE TABLE operators (
    id UUID PRIMARY KEY,
    badge_number VARCHAR(50) NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    assigned_shift VARCHAR(20) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE TABLE maintenance_logs (
    id UUID PRIMARY KEY,
    machine_id UUID NOT NULL REFERENCES machines(id),
    technician_id UUID NOT NULL REFERENCES operators(id),
    maintenance_type VARCHAR(30) NOT NULL,
    scheduled_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    start_time TIMESTAMP WITHOUT TIME ZONE,
    end_time TIMESTAMP WITHOUT TIME ZONE,
    parts_replaced JSONB NOT NULL DEFAULT '[]'::jsonb,
    operational_notes TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED'
);
-- Core Indexing Specifications for Sub-Millisecond Search Optimization
CREATE INDEX idx_telemetry_machine_timestamp ON telemetry(machine_id, timestamp DESC);
CREATE INDEX idx_telemetry_sensor_timestamp ON telemetry(sensor_id, timestamp DESC);
CREATE INDEX idx_alarms_state_severity ON alarms(state, severity);
CREATE INDEX idx_machine_events_type_time ON machine_events(machine_id, event_type, timestamp DESC);
CREATE INDEX idx_maintenance_machine ON maintenance_logs(machine_id, status);
