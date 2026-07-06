"""
IOB Phase 3 - Operational Simulation Scenarios (spec section 6)

Validates the framework against the three canonical emulation scenarios and the
downstream consumer each one targets:

  * Normal Steady State   -> sinusoidal oscillation + low Gaussian noise
                             (Member 1: Backend ingestion / baseline load)
  * Asset Thermal Failure  -> value steps past ``max_limit`` and the status
                             string flips to ``LIMIT_CLAMPED``
                             (Member 3: AI engine anomaly / predictive health)
  * Emergency Stop (E-Stop)-> values drop instantly to zero or to the sensor's
                             environmental ambient reference base point
                             (Member 4: Frontend hazard alerting)
"""

import statistics
import time

from constants import STATE_ALARM, STATE_EMERGENCY_STOP, STATE_RUNNING
from factory import FactorySimulatorOrchestrator
from machine import MachineInstance
from sensor import SensorSimulator
from telemetry import TelemetryBuilder


def _find_machine(orchestrator, machine_type):
    return next(m for m in orchestrator.machines if m.type == machine_type)


# --------------------------------------------------------------------------
# Scenario 1 - Normal Steady State (Member 1: Backend ingestion)
# --------------------------------------------------------------------------
def test_normal_steady_state_oscillation_and_noise():
    orchestrator = FactorySimulatorOrchestrator()
    robot = _find_machine(orchestrator, "ASSEMBLY_ROBOT")
    robot.current_state = STATE_RUNNING
    robot.state_timer = 0.0

    now = time.time()
    readings = []
    for _ in range(40):
        now += 1.0  # 1s synthetic steps, above the 1 Hz temperature interval
        for sensor in robot.tick(now, 1.0):
            if sensor.type == "TEMPERATURE":
                readings.append(sensor.current_value)

    # Enough samples to make statistical assertions meaningful
    assert len(readings) > 5

    # All within the physical envelope and carrying a healthy status
    assert all(20.0 <= value <= 120.0 for value in readings)
    assert all(
        TelemetryBuilder.generate_json_envelope(orchestrator.factory_meta, robot, s)["quality"]
        == "GOOD"
        for s in robot.sensors
        if s.type == "TEMPERATURE"
    )

    # Centred on the ~65 C base operating point (sinusoidal + low noise)
    assert abs(statistics.mean(readings) - 65.0) < 5.0

    # Non-constant: sinusoidal drift + Gaussian noise are both present
    assert statistics.pstdev(readings) > 0.01


# --------------------------------------------------------------------------
# Scenario 2 - Asset Thermal Failure (Member 3: AI / predictive health)
# --------------------------------------------------------------------------
def test_asset_thermal_failure_clamps_to_limit():
    orchestrator = FactorySimulatorOrchestrator()

    # A bearing sensor running hot: its safe envelope is exceeded under high
    # mechanical load (ALARM state), emulating progressive thermal runaway.
    failing_cfg = {
        "sensor_sub_id": "BRG01_TE01",
        "name": "Bearing Temperature",
        "type": "TEMPERATURE",
        "min_range": 0.0,
        "max_range": 100.0,
        "unit": "CELSIUS",
        "frequency_hz": 1000.0,  # sample immediately
        "noise_variance": 0.0,
        "failure_probability": 0.0,
    }
    pump_cfg = {
        "machine_id": "GMC_AUS_ASY_WLD01_PMP02",
        "name": "Cooling Loop Recirculation Pump",
        "type": "INDUSTRIAL_PUMP",
        "manufacturer": "GRUNDFOS",
        "production_line": "WLD01",
    }
    machine = MachineInstance(pump_cfg, [failing_cfg])
    sensor = machine.sensors[0]
    sensor.base_value = 80.0  # degraded bearing approaching its thermal limit

    machine.current_state = STATE_ALARM
    machine.state_timer = 0.0

    now = sensor.last_sampled_time + 0.01
    assert sensor.execute_sampling_tick(STATE_ALARM, now) is True

    # Value steps past max_limit and the status string flips to LIMIT_CLAMPED
    assert sensor.quality == "LIMIT_CLAMPED"
    assert sensor.current_value == 100.0

    # Downstream Member 3 sees the failure signature in the envelope
    envelope = TelemetryBuilder.generate_json_envelope(
        orchestrator.factory_meta, machine, sensor
    )
    assert envelope["value"] == 100.0
    assert envelope["quality"] == "LIMIT_CLAMPED"
    assert envelope["metadata"]["machine_state"] == STATE_ALARM


# --------------------------------------------------------------------------
# Scenario 3 - Emergency Stop (Member 4: Frontend hazard alerting)
# --------------------------------------------------------------------------
def test_emergency_stop_drops_to_zero_or_ambient():
    orchestrator = FactorySimulatorOrchestrator()
    robot = _find_machine(orchestrator, "ASSEMBLY_ROBOT")
    robot.current_state = STATE_EMERGENCY_STOP
    robot.state_timer = 0.0

    now = time.time()
    envelopes = []
    for _ in range(4):
        now += 0.5
        for sensor in robot.tick(now, 0.5):
            envelopes.append(
                TelemetryBuilder.generate_json_envelope(orchestrator.factory_meta, robot, sensor)
            )

    assert envelopes, "expected at least one sensor reading after E-Stop"
    assert all(
        env["metadata"]["machine_state"] == STATE_EMERGENCY_STOP for env in envelopes
    )

    for env in envelopes:
        if env["unit"] == "AMP":
            # Zero-ambient channel collapses instantly to zero
            assert env["value"] == 0.0
            assert env["quality"] == "GOOD"
        elif env["unit"] == "CELSIUS":
            # Temperature channel drops to its environmental ambient base point
            assert env["value"] == 20.0
            assert env["quality"] == "GOOD"
