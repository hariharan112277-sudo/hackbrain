-- Master Sample Data Script for Validation of Functional Interfaces
SET search_path TO industrial, public;

-- Seed Single Factory Compound Matrix
INSERT INTO plants (id, name, location) VALUES 
('e00bbdf8-2b28-48b8-b80c-03d3c14c514d', 'Stuttgart Assembly Complex Hub-4', 'Stuttgart, Germany');

-- Seed Linear Assembly Segment Elements
INSERT INTO production_lines (id, plant_id, name, sequence_number) VALUES 
('a7a3bfa4-61c1-4b13-899a-cbbf628b0821', 'e00bbdf8-2b28-48b8-b80c-03d3c14c514d', 'Main Powertrain Cell Line A', 1);

-- Seed Networking Gateway
INSERT INTO gateways (id, name, ip_address, mac_address, firmware_version, protocol, status) VALUES 
('c53b2160-b996-48c6-829d-ee18d7f45778', 'GW-EDGE-01', '10.142.41.5', '00:1A:2B:3C:4D:5E', 'v4.2.1-build82', 'MQTT', 'ONLINE');

-- Seed Heavy Dynamic Infrastructure Asset Tracking Rows
INSERT INTO assets (id, production_line_id, name, category, manufacturer, model, serial_number, criticality, installation_date, status) VALUES 
('f65efea9-a1b1-4f11-92be-154a4f89d311', 'a7a3bfa4-61c1-4b13-899a-cbbf628b0821', 'KUKA Titan Heavy Load Robotic Arm', 'Robotics', 'KUKA AG', 'KR-1000-TITAN', 'SN-KUKA-992182', 'Mission-Critical', '2025-01-15 08:00:00', 'ONLINE');

-- Seed Mapping Variable Linkage Mapped Row Data
INSERT INTO machines (id, asset_id, gateway_id, firmware_version, operating_hours, runtime_counter, current_mode) VALUES 
('182bcfb2-4d1a-4da2-9b24-9dfc120fb211', 'f65efea9-a1b1-4f11-92be-154a4f89d311', 'c53b2160-b996-48c6-829d-ee18d7f45778', 'firmware-kuka-v9.1', 1240.5, 340.2, 'AUTOMATIC');

-- Seed Target Sensing Nodes
INSERT INTO sensors (id, machine_id, name, sensor_type, measurement_unit, sampling_rate_hz, status) VALUES 
('bd5bcefa-9fa1-4191-88bc-41829daff911', '182bcfb2-4d1a-4da2-9b24-9dfc120fb211', 'Axis-3 Vibration Node', 'Vibration', 'mm/s', 1000.0, 'ONLINE'),
('293bcffa-1ab2-41f2-99ca-2182bba11411', '182bcfb2-4d1a-4da2-9b24-9dfc120fb211', 'Primary Windings Temp Thermal Couple', 'Temperature', 'Celsius', 10.0, 'ONLINE');

-- Seed Engineering Team Members
INSERT INTO operators (id, badge_number, first_name, last_name, assigned_shift, is_active) VALUES 
('518bcffa-99ab-4411-bc29-4182baaa9115', 'BADGE-8821', 'Dieter', 'Eisler', 'DAY', TRUE);
