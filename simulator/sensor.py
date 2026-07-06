"""
IOB Phase 3 - Sensor Simulator

Logical digital twin representation of an individual physical
instrumentation element.
"""

import random
import time
from typing import Any, Dict

from generator import PhysicsWaveformEngine


class SensorSimulator:
    """
    Logical digital twin representation of an individual physical
    instrumentation element.
    """

    def __init__(self, machine_id: str, cfg: Dict[str, Any]):
        self.machine_id: str = machine_id
        self.sensor_id: str = f"{machine_id}_{cfg['sensor_sub_id']}"
        self.name: str = cfg["name"]
        self.type: str = cfg["type"]
        self.min_range: float = float(cfg["min_range"])
        self.max_range: float = float(cfg["max_range"])
        self.unit: str = cfg["unit"]
        self.frequency_hz: float = float(cfg["frequency_hz"])
        self.noise_variance: float = float(cfg["noise_variance"])
        self.failure_probability: float = float(cfg["failure_probability"])

        # Internal State Registers
        self.base_value: float = (self.max_range - self.min_range) * 0.45 + self.min_range
        self.drift_accumulator: float = 0.0
        self.current_value: float = self.base_value
        self.quality: str = "GOOD"
        self.last_sampled_time: float = time.time()
        self.sequence_number: int = 0

    def execute_sampling_tick(self, machine_state: str, current_time: float) -> bool:
        """
        Evaluates run-time step loops against targeted tracking sample frequencies.
        """
        elapsed = current_time - self.last_sampled_time
        target_interval = 1.0 / self.frequency_hz

        if elapsed >= target_interval:
            # Emulate linear drift degradation over long running cycles
            self.drift_accumulator += 0.00001 * random.uniform(-1.0, 1.5)

            # Injection of spontaneous hardware connection drops
            if random.random() < self.failure_probability:
                self.quality = "BAD_TIMEOUT"
                self.current_value = -999.0
            else:
                self.current_value, self.quality = PhysicsWaveformEngine.compute_next_value(
                    state=machine_state,
                    base_val=self.base_value,
                    elapsed_time=current_time,
                    noise_var=self.noise_variance,
                    drift_acc=self.drift_accumulator,
                    limits=(self.min_range, self.max_range),
                )

            self.sequence_number += 1
            self.last_sampled_time = current_time
            return True
        return False
