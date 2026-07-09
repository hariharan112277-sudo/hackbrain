# Operational Scenario Specifications & State Vectors

This document defines the deterministic state patterns used to populate future simulators without deviating from frozen contracts.

### 1. Nominal Scenarios

#### Scenario A: Nominal Production Cycle
*   **Sequence Timeline**:
    1. Machine sets state variable to 02: WARM_UP. Spindle current spikes momentarily to 45A, temperature rises gradually from ambient room temperature ($21^\circ\text{C}$) to $42^\circ\text{C}$.
    2. Transition to 03: PRODUCTION. Vibration settles into a standard steady-state harmonic rhythm ($12.4\ m/s^2$ average). Current usage forms a predictable cyclical wave matching the physical cutting pass.
*   **Expected Behavior**: Clean telemetry stream. Zero anomalies flagged by downstream logic.

#### Scenario B: Scheduled Maintenance Rollout
*   **Sequence Timeline**:
    1. Production cycle stops at predefined work boundary. State transitions smoothly to 01: IDLE, then to 04: MAINTENANCE.
    2. Telemetry payload flags data quality markers as VALID_MAINTENANCE_WINDOW.
*   **Expected Behavior**: Threshold engines pause active alarm logging for the designated asset duration.

### 2. Degraded & Failure Scenarios

#### Scenario C: Bearing Wear Mechanical Degradation
*   **Sequence Timeline**:
    1. Continuous operation in state 03: PRODUCTION.
    2. Over a projected timeline simulation window, SN_VIB_XYZ_01 shows a continuous upward slope in root-mean-square (RMS) energy.
    3. Concurrently, SN_TMP_CORE_02 increases by $15\%$, reflecting increased frictional resistance.
*   **Expected Behavior**: Parser tags entries with an elevated risk factor; validation logs pass data transparently to Member 3's Knowledge Graph to build anomaly vectors.

#### Scenario D: Emergency Stop Event (E-Stop)
*   **Sequence Timeline**:
    1. Instantaneous state transition from 03: PRODUCTION directly to 05: FAULTED.
    2. Current readings drop to 0.0A within 85 milliseconds. Vibration registers a single massive deceleration spike, followed immediately by absolute silence.
*   **Expected Behavior**: The Subscriber catches the sudden state change and immediately generates a high-priority alarm row inside the relational tables.

### Integration with hackbrain repo
Operational scenarios map directly to the existing telemetry and state-machine wiring for deterministic simulation and downstream GraphRAG ingestion.