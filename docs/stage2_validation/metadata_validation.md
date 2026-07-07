# Asset Metadata Structural Validation

**Stage:** 2 — Contract Validation, Alignment & Audit
**Owner:** Member 2 (Industrial Operating Brain — Data Foundation)
**Document ID:** `ASSET-META-VAL-v1.0`
**Standards Alignment:** ISA-95 Part 2 Equipment Hierarchy, ISO 8601, RFC 8259
**Audit Date:** 2026-07-07 (UTC)
**Contract Baseline:** Canonical Stage 1 generation (`iob_data_engine` / `config/machines.yaml`, `config/sensors.yaml`)

---

## 1. Purpose & Scope

Validates the structural taxonomy used to contextually define machine assets, calibration constraints, and their structural hierarchy within the asset tree.

---

## 2. Structural Taxonomy Representation

```yaml
asset_hierarchy:
  enterprise: "IOB_Global_Manufacturing"
  site: "site_alpha"
  area: "area_machining"
  device:
    id: "DEV_CNC_001"
    type: "5-Axis CNC Milling Machine"
    manufacturer: "IndustrialMachinesCorp"
    model_year: 2024
    sensors:
      - id: "SNS_SPINDLE_01"
        type: "Rotary Speed Sensor"
        unit: "RPM"
        calibration_offset: 0.00
        min_threshold: 0.0
        max_threshold: 12000.0
      - id: "SNS_VIB_01"
        type: "Triaxial Accelerometer"
        unit: "G"
        calibration_offset: +0.02
        min_threshold: 0.0
        max_threshold: 5.0
```

**Audit verification:** The taxonomy is a clean ISA-95 Part 2 equipment decomposition (Enterprise → Site → Area → Device → Sensor). `device.id` (`DEV_CNC_001`) matches `config/simulator_config.yaml`; `sensors[].id` (`SNS_SPINDLE_01` / `SNS_VIB_01`), units (`RPM` / `G`), `calibration_offset`, and `min/max_threshold` resolve directly to `config/sensors.yaml` and the telemetry JSON contract (`json_contract_validation.md` §2.1). The `enterprise → site → area → device` spine matches the UNS topic path consumed by the ingestion `NormalizationEngine`, guaranteeing that static metadata and live telemetry resolve to the same asset node.

---

## 3. Alignment Audit

- **Asset Mapping:** Every simulated metric mapped inside Section 1 (MQTT topology) and Section 2 (JSON payload structures) correlates directly to an asset defined within this metadata profile.
- **Integration Vector:** This dictionary provides structural data fields that Member 3 can import directly into their Knowledge Graph schema definitions.
- **Verdict:** **COMPLIANT**.
