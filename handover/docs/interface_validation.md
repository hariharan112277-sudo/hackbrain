# System Interface Integrity Manifest (Task 2 Interface Validation)

```text
Legend:
  [STABLE]   - Design frozen. Underlying structural contracts cannot be changed.
  [EVOLVING] - Architecture open to extension. Allows addition of custom properties.
```

### 1. `IMachineRegistryService` — `[STABLE]`
* **Purpose:** Acts as the single source of truth for downstream service queries about physical factory equipment.
* **Component Owner Allocation:** Created and maintained by **Member 2**; consumed directly by **Member 1** APIs.
* **Compatibility & Backward Mapping Strategy:** Uses explicit, immutable dictionary parameters to insulate core tables from changes in the UI or schema definitions.

### 2. `ISensorRegistryService` — `[STABLE]`
* **Purpose:** Manages hardware definitions, physical calibrations, and operating threshold parameters.
* **Component Owner Allocation:** Created and maintained by **Member 2**; consumed directly by **Member 1** APIs.
* **Compatibility & Backward Mapping Strategy:** Uses deterministic Pydantic V2 parsing fields to maintain complete backward compatibility across all hardware upgrades.

### 3. `IHistoricalQueryService` — `[EVOLVING]`
* **Purpose:** Handles complex windowed lookups and statistical calculations for historical time-series blocks.
* **Component Owner Allocation:** Created and maintained by **Member 2**; consumed by **Member 1** (REST APIs) and **Member 3** (Analytics).
* **Compatibility & Backward Mapping Strategy:** Protects database performance by restricting query boundaries to a maximum 30-day lookback window unless overridden by specific system parameters.

### 4. `IMQTTIntegrationService` — `[STABLE]`
* **Purpose:** Standardizes broker topics, monitors subscription connections, and exposes live message streams.
* **Component Owner Allocation:** Created and maintained by **Member 2**; consumed by **Member 1** (Real-time Websockets Interface).
* **Compatibility & Backward Mapping Strategy:** Enforces a rigid, append-only topic structure to prevent disruption of downstream consumer applications.
