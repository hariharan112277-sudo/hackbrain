-- Industrial Operating Brain (IOB) — Frozen Core Schema (Part 2.1)
-- Track A (Database Layer) — Stage 1
--
-- This is the exact, frozen schema that app/models/{user,asset,alarm}.py map
-- onto via SQLAlchemy. Do not redesign these tables — if a field is genuinely
-- missing, write a migration and message the team the same day (Part 2.1).
--
-- Mounted into the postgres container's /docker-entrypoint-initdb.d so a
-- fresh `docker compose up` boots with the tables Track A's API expects,
-- without requiring a manual `Base.metadata.create_all()` step first.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS assets (
    asset_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    plant_id VARCHAR(20) NOT NULL,
    line_id VARCHAR(20) NOT NULL,
    machine_id VARCHAR(20) NOT NULL UNIQUE,
    asset_type VARCHAR(60),
    install_date DATE,
    criticality VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sensors (
    sensor_id VARCHAR(20) PRIMARY KEY,
    asset_id VARCHAR(20) REFERENCES assets(asset_id),
    metric_name VARCHAR(60) NOT NULL,
    unit VARCHAR(20),
    min_range NUMERIC,
    max_range NUMERIC
);

CREATE TABLE IF NOT EXISTS telemetry (
    id BIGSERIAL PRIMARY KEY,
    asset_id VARCHAR(20) REFERENCES assets(asset_id),
    ts TIMESTAMPTZ NOT NULL,
    temperature_c NUMERIC,
    pressure_bar NUMERIC,
    vibration_mm_s NUMERIC,
    rpm NUMERIC,
    voltage_v NUMERIC,
    current_a NUMERIC,
    energy_kwh NUMERIC,
    status VARCHAR(20)
);

CREATE INDEX IF NOT EXISTS idx_telemetry_asset_ts ON telemetry (asset_id, ts DESC);

CREATE TABLE IF NOT EXISTS events (
    event_id BIGSERIAL PRIMARY KEY,
    asset_id VARCHAR(20) REFERENCES assets(asset_id),
    ts TIMESTAMPTZ NOT NULL,
    event_type VARCHAR(40),
    description TEXT
);

CREATE TABLE IF NOT EXISTS alarms (
    alarm_id VARCHAR(30) PRIMARY KEY,
    asset_id VARCHAR(20) REFERENCES assets(asset_id),
    severity VARCHAR(20),
    code VARCHAR(40),
    message TEXT,
    value NUMERIC,
    threshold NUMERIC,
    ts TIMESTAMPTZ NOT NULL,
    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_alarms_asset ON alarms (asset_id, resolved);

CREATE TABLE IF NOT EXISTS maintenance_logs (
    id BIGSERIAL PRIMARY KEY,
    asset_id VARCHAR(20) REFERENCES assets(asset_id),
    performed_at TIMESTAMPTZ,
    description TEXT,
    technician VARCHAR(80)
);

CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(120),
    role VARCHAR(20) NOT NULL DEFAULT 'viewer',
    created_at TIMESTAMPTZ DEFAULT now()
);
