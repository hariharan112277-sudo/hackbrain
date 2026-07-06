# Enterprise Architecture Governance & Change Control Board (CCB) Charter

**Platform:** Industrial Operating Brain (IOB)  
**Document Owner:** Principal Industrial IoT Platform Owner  
**Governance Scope:** Schema Evolutions, MQTT Topics, JSON Contracts, & Repository Interfaces

---

## 1. Governance Charter & CCB Mandate

The **Architecture Governance Charter** establishes the formal compliance gates controlling any modifications to the Industrial Operating Brain platform. Once Version 1.0 is released to production, **ad-hoc schema edits, undocumented topic changes, or breaking interface alterations are strictly prohibited.**

Every structural change must be reviewed and approved by the **IOB Change Control Board (CCB)**, chaired by the Platform Owner, with mandatory sign-offs from Lead Backend, Lead AI/ML, and Lead Operations architects.

---

## 2. Strict Compatibility & Deprecation Governance

### 2.1 Backward Compatibility Guarantee
* **JSON Schema Contracts:** Any changes to `iob_telemetry_v1.json` or `iob_alarm_v1.json` must follow an **append-only strategy**. Existing field tokens (`timestamp`, `machine_id`, `measured_value`, `quality_code`) cannot be renamed, repurposed, or deleted. Adding optional attributes requires default value fallbacks.
* **Repository Abstraction Interfaces:** Interfaces defined in `interfaces.py` (`IMachineRepository`, `IMachineRegistryService`, `IHistoricalQueryService`) are frozen contracts. New repository capabilities must be introduced via interface extension or new service protocols (`e.g., IMachineRegistryServiceV2`).

### 2.2 Deprecation Lifecycle Protocol
When a contract or topic structure must be deprecated:
1. **Announcement Phase (Release N):** Mark contract as `[DEPRECATED]` in documentation; emit runtime warning logs when deprecated endpoints/topics are accessed.
2. **Migration Window (Minimum 180 Days):** Maintain dual-support running both old and new contracts simultaneously.
3. **Sunset Phase (Release N+2):** Remove deprecated code paths only after confirming zero downstream consumer traffic via audit logs.

---

## 3. Schema & Topic Governance Matrix

| Architectural Domain | Core Artifact / Contract | Stability Status | Authorized Modification Strategy | Governance Gate Required |
| :--- | :--- | :--- | :--- | :--- |
| **MQTT Messaging Fabric** | `industrial/iob/locations/...` | **[STABLE]** | Append sub-topics only; no alteration of hierarchy segments. | CCB Majority Approval |
| **Ingestion Schema** | `iob_telemetry_v1.json` | **[STABLE]** | Add optional properties (`additionalProperties` remains `false`). | Platform Owner + Lead AI Sign-off |
| **Persistence DDL** | `schema.sql` (TimescaleDB) | **[STABLE]** | Add nullable columns or indices via Alembic migration scripts. | DBA + Platform Owner Sign-off |
| **Integration DTOs** | `contracts.py` (`MachineDTO`) | **[STABLE]** | Non-breaking Pydantic V2 field additions with defaults. | Backend Lead + Platform Owner |
| **Historical Queries** | `IHistoricalQueryService` | **[EVOLVING]** | Add specialized filtering parameters within 30-day window limits. | Platform Owner Approval |
