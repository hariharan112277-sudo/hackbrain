# Sensor Architecture, Physical Characteristics & Maintenance Models

### 1. Sensor Instrumentation Profiles

#### Sensor Profile 01: Triaxial High-Frequency Accelerometer
*   **Sensor ID**: SN_VIB_XYZ_01
*   **Physical Metric**: Structural Vibration / Mechanical Accel.
*   **Engineering Unit**: Meters per second squared ($m/s^2$)
*   **Sampling Frequency**: 2.5 kHz base, downsampled to 10 Hz telemetry payloads.
*   **Operational Range**: $0.0 \text{ to } 500.0\ m/s^2$
*   **Threshold Hierarchy**:
    *   *Nominal Range*: $\le 120.0\ m/s^2$
    *   *Warning Limit*: $> 120.0 \text{ and } \le 180.0\ m/s^2$
    *   *Critical Limit*: $> 180.0\ m/s^2$
*   **Failure Modes**: Piezoelectric crystal degradation (manifests as continuous zero-offset drift), cable shielding breakage (manifests as high-frequency pink noise saturation).
*   **Calibration Protocol**: Semi-annual reference shaker calibration via ISO 16063-21 methods.

#### Sensor Profile 02: Thermocouple Core Thermal Array
*   **Sensor ID**: SN_TMP_CORE_02
*   **Physical Metric**: Spindle Core Operating Temperature.
*   **Engineering Unit**: Degrees Celsius (°C)
*   **Sampling Frequency**: 1 Hz
*   **Operational Range**: $-40.0^\circ\text{C to } 850.0^\circ\text{C}$
*   **Threshold Hierarchy**:
    *   *Nominal Range*: $15.0^\circ\text{C to } 75.0^\circ\text{C}$
    *   *Warning Limit*: $> 75.0^\circ\text{C and } \le 95.0^\circ\text{C}$
    *   *Critical Limit*: $> 95.0^\circ\text{C}$
*   **Failure Modes**: Junction open-circuit (hard return value of NaN or 999.9), thermal-well scaling (manifests as extreme first-order response time lag).
*   **Calibration Protocol**: Annual multi-point dry-block calibrator alignment checking.

#### Sensor Profile 03: Spindle Drive Amperage Current Transducer
*   **Sensor ID**: SN_CRT_DRV_03
*   **Physical Metric**: Three-Phase Input Alternating Current.
*   **Engineering Unit**: Amperes (A)
*   **Sampling Frequency**: 100 Hz
*   **Operational Range**: $0.0 \text{ to } 150.0\text{ A}$
*   **Threshold Hierarchy**:
    *   *Nominal Range*: $\le 90.0\text{ A}$
    *   *Warning Limit*: $> 90.0 \text{ and } \le 125.0\text{ A}$
    *   *Critical Limit*: $> 125.0\text{ A}$
*   **Failure Modes**: CT core saturation (clipping behavior at max peak value), phase imbalance anomalies.
*   **Calibration Protocol**: Bi-annual shunt voltage accuracy verification.

### Integration with hackbrain repo
Sensor profiles, thresholds, and failure modes are structured for direct ingestion into the Unified Namespace and GraphRAG pipelines.