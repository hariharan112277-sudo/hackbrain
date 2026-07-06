"""
Sensor Registry Service Module.
Re-exports SensorRegistryService from registry for clean DDD domain isolation.
"""
from integration.registry import SensorRegistryService

__all__ = ["SensorRegistryService"]
