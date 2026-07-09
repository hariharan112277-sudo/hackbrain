# Industrial Machine Inventory & Operational Profiles

### 1. Asset Inventory Profiles

#### Machine Asset 01: Multi-Axis CNC Milling Center
*   **Asset ID**: MC_CNC_01_A
*   **Type Identifier**: SUBTRACTIVE_MILL_V4
*   **Operational Mandate**: High-velocity physical subtraction of metal alloys under strictly controlled structural conditions.
*   **Physical Dependencies**: Interlocked 3-phase power supply, coolant pressurization lines, pneumatic clamping systems.
*   **Downstream Impact**: Drives structural geometry correctness; variations trigger downstream structural stress analysis failures.

#### Machine Asset 02: 6-Axis Industrial Articulated Robotic Arm
*   **Asset ID**: MC_ROB_02_B
*   **Type Identifier**: ARTICULATED_PAYLOAD_ROBOT
*   **Operational Mandate**: Precision pathing, heavy workpiece positioning, component alignment, and spot-welding operations.
*   **Physical Dependencies**: High-amperage braking systems, multi-axis servo controllers, fieldbus feedback arrays.
*   **Downstream Impact**: Controls cycle-time throughput; erratic movement paths indicate immediate kinetic degradation.

### 2. State Machine Model (OMAC PackML / ISA-88 Compliant)
All machines obey a deterministic state progression chart to enable accurate predictive anomaly scoring by Member 3.

```
[ 01: IDLE ]  ───────────> [ 02: WARM_UP ]
     ▲                            │
     │ (Stop Command)             ▼
[ 06: SHUTDOWN ] <────────── [ 03: PRODUCTION ]
     ▲                            │
     │ (Fault Event)              ▼
[ 05: FAULTED ]  <────────── [ 04: MAINTENANCE ]
```

*   **01: IDLE**: Control systems active; zero energy flowing to physical actuators.
*   **02: WARM_UP**: Low-speed calibration cycles executed to reach nominal operational temperatures.
*   **03: PRODUCTION**: Standard operating parameters; continuous streaming telemetry active.
*   **04: MAINTENANCE**: Local isolation mode; access keys checked, system restricted to step-by-step jog actions.
*   **05: FAULTED**: Automated safety trip occurred; physical brakes locked, error code latched to metadata registry.
*   **06: SHUTDOWN**: Controlled power dissipation sequence across sub-modules.

### Integration with hackbrain repo
State machine definitions and asset profiles are ready for MQTT topic mapping and downstream Member 3 anomaly models.