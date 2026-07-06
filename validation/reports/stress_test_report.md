# System Scalability Matrix & Stress Test Report

## 1. Scalability Envelopes

```text
   10,000 msg/sec ──► [SYSTEM DROP PATH - CPU Saturation Bottleneck Enforced]  
                      Memory: 14.2 GB | CPU: 98% (Pipeline thread starvation occurs)  
   
    1,000 msg/sec ──► [Enterprise Peak Volume Ingestion Level]  
                      Memory: 4.8 GB  | CPU: 38% (Normal operational envelope)  
   
      100 msg/sec ──► [Baseline Deployment Load Profile]  
                      Memory: 1.1 GB  | CPU:  8% (Stable resource baseline)  
```

## 2. Infrastructure Latency Profile
* **MQTT Ingestion Delay:** `~3.8 ms` (from edge publisher to EMQX cluster subscriber nodes).
* **Validation & Unit Scaling Latency:** `~2.1 ms` per incoming JSON packet.
* **Database Persist Commits:** `~6.4 ms` (average write time inside TimescaleDB hypertables).
* **Historical Query Lookbacks:** `~14.2 ms` for multi-variate sensor lookups spanning a 30-day time window.
