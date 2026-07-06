"""
IOB Phase 3 - Machine Instance

State-machine driven representation of physical enterprise manufacturing
equipment.
"""

import logging
from typing import Any, Dict, List

from constants import *
from sensor import SensorSimulator

logger = logging.getLogger("iob.simulator")


class MachineInstance:
    """
    State-machine driven representation of physical enterprise manufacturing
    equipment.
    """

    def __init__(self, machine_cfg: Dict[str, Any], sensor_templates: List[Dict[str, Any]]):
        self.machine_id: str = machine_cfg["machine_id"]
        self.name: str = machine_cfg["name"]
        self.type: str = machine_cfg["type"]
        self.manufacturer: str = machine_cfg["manufacturer"]
        self.production_line: str = machine_cfg["production_line"]

        # State Machine Initialization
        self.current_state: str = STATE_OFF
        self.operating_hours: float = 0.0
        self.state_timer: float = 0.0

        # Component Sensor Aggregation Instantiation
        self.sensors: List[SensorSimulator] = [
            SensorSimulator(self.machine_id, tpl) for tpl in sensor_templates
        ]

    def evaluate_state_machine_logic(self, delta_time: float):
        """
        Asynchronous internal state automation tracking execution loops.
        """
        self.state_timer += delta_time
        self.operating_hours += (delta_time / 3600.0)

        # Automatic deterministic cycle transitions for autonomous testing data flow
        if self.current_state == STATE_OFF and self.state_timer > 10.0:
            self._transition_to(STATE_STARTING)
        elif self.current_state == STATE_STARTING and self.state_timer > 15.0:
            self._transition_to(STATE_RUNNING)
        elif self.current_state == STATE_RUNNING and self.state_timer > 300.0:
            # Induce a preventive maintenance cycle for tracing
            self._transition_to(STATE_MAINTENANCE)
        elif self.current_state == STATE_MAINTENANCE and self.state_timer > 30.0:
            self._transition_to(STATE_STARTING)

    def _transition_to(self, target_state: str):
        logger.info(
            f"Asset Identity Matrix Shift [{self.machine_id}]: "
            f"{self.current_state} -> {target_state}"
        )
        self.current_state = target_state
        self.state_timer = 0.0

    def tick(self, current_time: float, delta_time: float) -> List[SensorSimulator]:
        """
        Advances the runtime counter clock ticks across internal child sensor elements.
        """
        self.evaluate_state_machine_logic(delta_time)
        activated_sensors = []

        for sensor in self.sensors:
            if sensor.execute_sampling_tick(self.current_state, current_time):
                activated_sensors.append(sensor)

        return activated_sensors
