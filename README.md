# Industrial Operating Brain (IOB) - Stage 3 Enterprise Data Foundation

## Member 2: Industrial IoT & Data Engineering Blueprint

### Executive Overview
This package establishes the Enterprise Industrial Data Architecture and Unified Namespace (UNS) structure for the Industrial Operating Brain (IOB). Adhering strictly to ISA-95 hierarchical models and ISA-88 batch/state definitions, this framework organizes real-world factory physics into highly validated relational metadata and telemetry streams ready for downstream Knowledge Graph (GraphRAG) parsing.

### Core Architecture Pillars
1. **Structural Determinism**: Flat hierarchy mapped to deterministic MQTT topics matching site/area/line/cell/device/telemetry.
2. **Schema Rigor**: Zero-tolerance serialization boundary at the Subscriber/Parser node via strict type casting and threshold containment.
3. **Downstream Ready**: Explicit relational mapping of failures, maintenance timelines, and raw telemetry to feed Member 3's anomaly detection models.

### Quick Start & Verification
- **Documentation Map**: See /docs/ for systemic details regarding sensor physics and operational states.
- **Validation Run**: Execute the validation checklists within /validation/ prior to triggering Stage 3B data generation.

### Integration Notes
- Fully decoupled from frontend/backend components.
- Preserves frozen interfaces.
- Ready for downstream AI/Knowledge Graph.
- Compatible with existing wiring in hackbrain repo.