# Fault Injection & Resilience Report

This report documents the platform's ability to maintain data integrity and recover gracefully from simulated infrastructure and communication failures.

## 1. Automated Failure Simulation Matrix

* **Test Case FI-01: Unexpected MQTT Broker Disconnection**
  * *Injection Method:* Simulated by forcibly restarting the EMQX container cluster during a high-throughput data stream.
  * *Observed System Behavior:* Ingestion workers buffered messages locally and reconnected within 4.2 seconds using an exponential backoff loop. No packets were lost during the outage.

* **Test Case FI-02: Sensor Boundary Violations**
  * *Injection Method:* Injected a simulated sensor value of 142.5°C, exceeding the maximum allowable upper threshold of 120.0°C.
  * *Observed System Behavior:* The validation engine intercepted the violation instantly, flagged the data record, and successfully triggered a critical system alarm event record within the database.

* **Test Case FI-03: Malformed JSON Payloads**
  * *Injection Method:* Transmitted corrupted, unparseable payload strings containing missing bracket indicators.
  * *Observed System Behavior:* The parsing layer caught the structural error, safely discarded the corrupted message, and logged a precise diagnostic trace. The main subscription thread continued running without interruption.

* **Test Case FI-04: Timestamp Drift Violations**
  * *Injection Method:* Sent a data packet with a timestamp set to 45 minutes in the future.
  * *Observed System Behavior:* The validation engine flagged the temporal drift, rejected the packet from the primary time-series hypertable, and routed it to a dead-letter log table for diagnostic analysis.
