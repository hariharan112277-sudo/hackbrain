"""
IOB Phase 3 - Factory Simulator Orchestrator

Main runtime execution orchestration loop. Coordinates state updates and
channels data outbound via the MQTT publishing engine layers.
"""

import logging
import os
import time
from typing import List, Optional

from config import ConfigManager
from machine import MachineInstance
from publisher import MqttPublisherEngine
from telemetry import TelemetryBuilder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("iob.orchestrator")


class FactorySimulatorOrchestrator:
    """
    Main runtime execution orchestration loop. Coordinates state updates and
    channels data outbound via the MQTT publishing engine layers.
    """

    def __init__(
        self,
        config_dir: Optional[str] = None,
        publisher: Optional[MqttPublisherEngine] = None,
    ):
        self.running = True

        # Load explicit declarative configurations
        self.config: ConfigManager = ConfigManager(config_dir)
        self.factory_meta: dict = self.config.factory_metadata
        self.mqtt_settings: dict = self.config.mqtt_settings

        # Instantiate architectural engines
        self.publisher = publisher or MqttPublisherEngine(self.mqtt_settings)

        self.machines: List[MachineInstance] = []
        for m_cfg in self.config.machines:
            m_type = m_cfg["type"]
            templates = self.config.sensor_templates.get(m_type, [])
            self.machines.append(MachineInstance(m_cfg, templates))

    def run(self, max_duration: Optional[float] = None):
        """
        Execute the emulation loops.

        :param max_duration: If set, run for at most this many seconds and then
            shut down gracefully. If ``None`` (or 0), run until interrupted.
        """
        logger.info("Initializing runtime simulation container engine process blocks...")
        self.publisher.start()

        last_time = time.time()
        start_time = last_time
        logger.info(
            f"Emulation loops fully active. Tracked targets: "
            f"{len(self.machines)} operational machines."
        )

        try:
            while self.running:
                current_time = time.time()
                delta_time = current_time - last_time

                if max_duration and (current_time - start_time) >= max_duration:
                    logger.info("Configured max duration reached; terminating emulation.")
                    break

                # Loose throttle step constraint loop targeting 10ms evaluations
                if delta_time < 0.01:
                    time.sleep(0.005)
                    continue

                for machine in self.machines:
                    active_sensors = machine.tick(current_time, delta_time)

                    for sensor in active_sensors:
                        payload = TelemetryBuilder.generate_json_envelope(
                            self.factory_meta, machine, sensor
                        )
                        self.publisher.send(
                            topic=payload["topic"],
                            payload=payload,
                            qos=int(self.mqtt_settings.get("qos_telemetry", 0)),
                        )

                last_time = current_time
        except KeyboardInterrupt:
            logger.info("Termination signal caught. Safely shutting down engines...")
        finally:
            self.publisher.stop()
            logger.info("Infrastructure runtime layers successfully released.")

    def run_forever(self):
        """Run until a termination signal is received."""
        self.run(max_duration=None)


if __name__ == "__main__":
    # Allow an ephemeral run for smoke testing without a broker, e.g.
    #   IOB_MAX_DURATION=5 IOB_LOG_OFFLINE=1 python simulator/factory.py
    duration = float(os.environ.get("IOB_MAX_DURATION", "0") or "0")
    FactorySimulatorOrchestrator().run(max_duration=duration or None)
