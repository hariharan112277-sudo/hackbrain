# MQTT Communication Contract Freeze (Task 3)

## 1. Topic Hierarchy Tree Structure

```text
industrial/  
  └── iob/  
        ├── site-global/  
        │     └── health/status                      [JSON Broadcast - Retained]  
        └── locations/  
              └── {factory_site_id}/  
                    └── lines/  
                          └── {production_line_id}/  
                                └── machines/  
                                      └── {machine_id}/  
                                            ├── telemetry    [QoS 1 - Unretained]  
                                            ├── alarms       [QoS 2 - Retained]  
                                            └── commands     [QoS 2 - Unretained]  
```

## 2. Operational Rules & Policies
* **Quality of Service (QoS) Strategy:**
  * **Telemetry Data Streams:** Set to **QoS 1 (At least once)**.
  * **System Critical Alarms & Commands:** Set to **QoS 2 (Exactly once)**.
* **Retained Message Policy:**
  * **Alarms:** Active alarms must be marked with a `Retained` flag.
  * **Telemetry Streams:** Must **never** be retained.
* **Topic Naming Standards:** Lowercase alphanumeric characters separated by single hyphens (`-`).
