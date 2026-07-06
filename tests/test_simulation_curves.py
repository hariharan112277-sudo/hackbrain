"""
IOB Phase 3 - Simulation Curve & Core Behaviour Tests

Validates the physics waveform engine, sensor sampling, machine state-machine
transitions, telemetry envelope construction, configuration loading and the
end-to-end publishing path (including OFFLINE operation without a broker).
"""

import time

from config import ConfigManager
from constants import STATE_ALARM, STATE_MAINTENANCE, STATE_OFF, STATE_RUNNING, STATE_STARTING
from factory import FactorySimulatorOrchestrator
from generator import PhysicsWaveformEngine
from machine import MachineInstance
from publisher import MqttPublisherEngine
from sensor import SensorSimulator
from telemetry import TelemetryBuilder


# --------------------------------------------------------------------------
# Physics Waveform Engine
# --------------------------------------------------------------------------
def test_running_state_tracks_base_value():
    value, quality = PhysicsWaveformEngine.compute_next_value(
        state=STATE_RUNNING, base_val=100.0, elapsed_time=0.0,
        noise_var=0.0, drift_acc=0.0, limits=(0.0, 1000.0),
    )
    assert quality == "GOOD"
    # multiplier 1.0; with zero elapsed time oscillation is 0
    assert abs(value - 100.0) < 1e-6


def test_off_state_is_near_zero():
    value, quality = PhysicsWaveformEngine.compute_next_value(
        state=STATE_OFF, base_val=100.0, elapsed_time=0.0,
        noise_var=0.0, drift_acc=0.0, limits=(0.0, 1000.0),
    )
    assert quality == "GOOD"
    assert value == 0.0  # multiplier 0.0 -> 0.0


def test_upper_clamp_sets_clamped_quality():
    value, quality = PhysicsWaveformEngine.compute_next_value(
        state=STATE_RUNNING, base_val=100.0, elapsed_time=0.0,
        noise_var=0.0, drift_acc=0.0, limits=(0.0, 50.0),
    )
    assert value == 50.0
    assert quality == "LIMIT_CLAMPED"


def test_lower_clamp_sets_clamped_quality():
    value, quality = PhysicsWaveformEngine.compute_next_value(
        state=STATE_RUNNING, base_val=-100.0, elapsed_time=0.0,
        noise_var=0.0, drift_acc=0.0, limits=(-10.0, 50.0),
    )
    assert value == -10.0
    assert quality == "LIMIT_CLAMPED"


def test_alarm_state_elevates_output():
    base = 100.0
    value, _ = PhysicsWaveformEngine.compute_next_value(
        state=STATE_ALARM, base_val=base, elapsed_time=0.0,
        noise_var=0.0, drift_acc=0.0, limits=(0.0, 10000.0),
    )
    # multiplier 1.45
    assert value > base


# --------------------------------------------------------------------------
# Sensor Simulator
# --------------------------------------------------------------------------
def _make_sensor(frequency_hz=1.0, failure_probability=0.0):
    cfg = {
        "sensor_sub_id": "TST01_V01",
        "name": "Test Sensor",
        "type": "VIBRATION",
        "min_range": 0.0,
        "max_range": 100.0,
        "unit": "mm/s",
        "frequency_hz": frequency_hz,
        "noise_variance": 0.0,
        "failure_probability": failure_probability,
    }
    return SensorSimulator("GMC_AUS_ASY_WLD01_TST01", cfg)


def test_sensor_respects_sample_interval():
    sensor = _make_sensor(frequency_hz=0.1)  # 10s interval
    now = sensor.last_sampled_time
    assert sensor.execute_sampling_tick(STATE_RUNNING, now + 0.5) is False
    assert sensor.sequence_number == 0
    assert sensor.execute_sampling_tick(STATE_RUNNING, now + 11.0) is True
    assert sensor.sequence_number == 1


def test_sensor_failure_sets_bad_quality():
    sensor = _make_sensor(frequency_hz=1000.0, failure_probability=1.0)
    now = sensor.last_sampled_time
    # failure_probability of 1.0 forces a BAD_TIMEOUT reading
    assert sensor.execute_sampling_tick(STATE_RUNNING, now + 0.01) is True
    assert sensor.quality == "BAD_TIMEOUT"
    assert sensor.current_value == -999.0


# --------------------------------------------------------------------------
# Machine State Machine
# --------------------------------------------------------------------------
def _make_machine(state=STATE_OFF):
    cfg = {
        "machine_id": "GMC_AUS_ASY_WLD01_ROB01",
        "name": "Test Robot",
        "type": "ASSEMBLY_ROBOT",
        "manufacturer": "KUKA",
        "production_line": "WLD01",
    }
    machine = MachineInstance(cfg, [])
    machine.current_state = state
    return machine


def test_machine_state_lifecycle():
    machine = _make_machine(STATE_OFF)
    assert machine.current_state == STATE_OFF

    machine.evaluate_state_machine_logic(11.0)
    assert machine.current_state == STATE_STARTING

    machine.evaluate_state_machine_logic(16.0)
    assert machine.current_state == STATE_RUNNING

    machine.evaluate_state_machine_logic(301.0)
    assert machine.current_state == STATE_MAINTENANCE

    machine.evaluate_state_machine_logic(31.0)
    assert machine.current_state == STATE_STARTING


def test_machine_operating_hours_accumulate():
    machine = _make_machine(STATE_RUNNING)
    machine.evaluate_state_machine_logic(3600.0)
    assert machine.operating_hours == 1.0


# --------------------------------------------------------------------------
# Telemetry Envelope
# --------------------------------------------------------------------------
def test_telemetry_envelope_structure():
    machine = _make_machine(STATE_RUNNING)
    sensor = _make_sensor(frequency_hz=1000.0)
    sensor.current_value = 42.0
    sensor.quality = "GOOD"
    sensor.sequence_number = 7

    factory_meta = {"enterprise": "GMC", "site": "AUS", "plant": "ASY"}
    envelope = TelemetryBuilder.generate_json_envelope(factory_meta, machine, sensor)

    expected_keys = {
        "timestamp", "asset_id", "machine_id", "sensor_id", "topic",
        "measurement", "value", "unit", "quality", "sequence_number",
        "gateway_id", "site_id", "plant_id", "line_id", "processing_status",
        "metadata",
    }
    assert expected_keys <= set(envelope.keys())
    assert envelope["value"] == 42.0
    assert envelope["quality"] == "GOOD"
    assert envelope["sequence_number"] == 7
    assert envelope["topic"] == "gmc/aus/asy/wld01/rob01/telemetry/vibration"
    assert envelope["gateway_id"] == "AUS_ASY_GW01"
    assert envelope["processing_status"] == "RAW"
    assert envelope["metadata"]["machine_state"] == STATE_RUNNING


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
def test_config_manager_loads_defaults():
    config = ConfigManager()
    assert config.enterprise == "GMC"
    assert len(config.machines) == 3
    types = {m["type"] for m in config.machines}
    assert types == {"ASSEMBLY_ROBOT", "CNC_MILL", "INDUSTRIAL_PUMP"}
    assert config.mqtt_settings["broker_port"] == 1883


# --------------------------------------------------------------------------
# End-to-end (offline, no broker required)
# --------------------------------------------------------------------------
def test_end_to_end_offline_publishing():
    captured = []

    def sink(topic, payload):
        captured.append((topic, payload))

    offline_settings = {
        "broker_host": "127.0.0.1",
        "broker_port": 1883,
        "client_id": "iob_test",
        "keepalive_sec": 60,
        "qos_telemetry": 0,
    }
    orchestrator = FactorySimulatorOrchestrator(
        publisher=MqttPublisherEngine(offline_settings, sink=sink)
    )

    now = time.time()
    for machine in orchestrator.machines:
        active = machine.tick(now + 1.0, 1.0)
        for sensor in active:
            payload = TelemetryBuilder.generate_json_envelope(
                orchestrator.factory_meta, machine, sensor
            )
            orchestrator.publisher.send(payload["topic"], payload)

    assert len(captured) >= 1
    topic, payload = captured[0]
    assert topic.startswith("gmc/aus/asy/")
    assert "value" in payload and "quality" in payload
