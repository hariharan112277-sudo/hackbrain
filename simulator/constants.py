"""
IOB Phase 3 - Simulation Engine System Constants
"""

# Machine Operational States (ISA-95 Equipment State model, extended)
STATE_OFF = "OFF"
STATE_STARTING = "STARTING"
STATE_RUNNING = "RUNNING"
STATE_IDLE = "IDLE"
STATE_WARNING = "WARNING"
STATE_ALARM = "ALARM"
STATE_STOPPING = "STOPPING"
STATE_MAINTENANCE = "MAINTENANCE"
STATE_FAULT = "FAULT"
STATE_EMERGENCY_STOP = "EMERGENCY_STOP"

# Ordered lifecycle used by deterministic autonomous cycle transitions
LIFECYCLE_STATES = (
    STATE_OFF,
    STATE_STARTING,
    STATE_RUNNING,
    STATE_IDLE,
    STATE_WARNING,
    STATE_ALARM,
    STATE_STOPPING,
    STATE_MAINTENANCE,
    STATE_FAULT,
    STATE_EMERGENCY_STOP,
)

# Sensor Data Quality Flags (OPC-UA / ISA-95 status semantics)
QUALITY_GOOD = "GOOD"
QUALITY_UNCERTAIN = "UNCERTAIN_DEGRADED"
QUALITY_BAD = "BAD_TIMEOUT"
QUALITY_CLAMPED = "LIMIT_CLAMPED"

# Sentinel value emitted when a sensor hardware link drops
SENSOR_FAILURE_VALUE = -999.0
