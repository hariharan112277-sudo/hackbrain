# 2. Complete Asset Hierarchy Specification

This specification utilizes an adapted **ISA-95 Part 1 Equipment Hierarchy Model**, extending it down to the sub-component and sensor layer to bridge Operational Technology (OT) and Information Technology (IT).

## 2.1 Operational Level Definitions

The hierarchy is comprised of eight structural tiers.

| Tier | Level Name       | ISA-95 Mapping      | Description                                      | Primary Functional Purpose                                      |
|------|------------------|---------------------|--------------------------------------------------|-----------------------------------------------------------------|
| L1   | Enterprise       | Enterprise          | Corporate entity driving global governance.      | Consolidates multi-site metrics, financial compliance, and global KPIs. |
| L2   | Site             | Site                | A distinct physical geographic location or campus. | Regional operational boundary, cost center analysis, supply chain node. |
| L3   | Plant            | Area                | A functional building or physical plant sector.  | Production scheduling, utility management, and localized resource pooling. |
| L4   | Production Line  | Work Cell / Line    | A continuous, batch, or discrete set of machines. | Operational throughput tracking, OEE (Overall Equipment Effectiveness) calculation. |
| L5   | Machine          | Equipment           | An individual unit of mechanical/electrical asset. | Direct asset lifecycle tracking, maintenance execution, job-routing execution. |
| L6   | Subsystem        | Unit / Module       | Critical component group within a machine.       | Isolation of mechanical failure points, root-cause isolation.  |
| L7   | Device           | Control Element     | Edge gateway, PLC, I/O block, or intelligent driver. | Protocol translation, local logic execution, and edge compute routing. |
| L8   | Sensor           | Control Point       | Individual transducer or physical instrument.    | Raw physical metric collection (voltage, pressure, vibration). |

## 2.2 Global Naming Conventions & Unique Identifier Strategy

To ensure global uniqueness across multi-national instances without relying on database auto-increment keys during ingestion, the IOB mandates a deterministic, hierarchical **Functional Location Identifier (FLUID)**.

- **Format String:** `[Enterprise]_[Site]_[Plant]_[Line]_[Machine]_[Subsystem]_[Device/Sensor]`
- **Character Constraints:** Uppercase alphanumeric characters only (`A-Z`, `0-9`). Separated exclusively by underscores (`_`). No spaces, hyphens, or special characters allowed.
- **Padding Rule:** Numeric indices within codes must be left-padded with zeros up to 3 digits (e.g., `LIN001` instead of `LIN1`).

### Example Hierarchy

```
[ENT] GLOBAL MANUFACTURING CORP (GMC)
│
└── [SIT] AUSTIN TEXAS PLANT (AUS)
     │
     └── [PLN] ASSEMBLY & PACKAGING (ASY)
          │
          └── [LIN] ROBOTIC WELDING LINE 1 (WLD01)
               │
               └── [MAC] MULTI-AXIS ARM ROBOT (ROB01)
                    │
                    └── [SUB] ARTICULATED WRIST AXIS 5 (WRI05)
                         │
                         └── [SNS] AXIS TEMPERATURE SENSOR (TE01)
```

**Deterministic UUID (v5) Rule:** For systems requiring fixed-width 128-bit identifiers (e.g., PostgreSQL primary keys, Graph nodes), a UUID v5 must be derived using the standard ISO OID namespace and the canonical string path representation of the FLUID:

`URN:IOB:FLUID:GMC_AUS_ASY_WLD01_ROB01_WRI05_TE01`

## 2.3 Asset Hierarchy Structural Schema

```mermaid
graph TD
    classDef default fill:#f9f9f9,stroke:#333,stroke-width:1px;
    classDef structural fill:#d4e6f1,stroke:#2980b9,stroke-width:2px;
    classDef physical fill:#d5f5e3,stroke:#27ae60,stroke-width:2px;
  
    L1[Enterprise: GMC] :::structural --> L2[Site: AUS] :::structural
    L2 --> L3[Plant: ASY] :::structural
    L3 --> L4[Production Line: WLD01] :::structural
    L4 --> L5[Machine: ROB01] :::physical
    L5 --> L6[Subsystem: WRI05] :::physical
    L6 --> L7[Device: GW01] :::physical
    L6 --> L8[Sensor: TE01] :::physical
```