# IOB Project & Team Boundary Matrix

## 1. Domain Mapping
The Industrial Operating Brain acts as a high-throughput, low-latency orchestration layer managing physical assets via Digital Twins, parsing failure vectors through Knowledge Graphs, and delivering Predictive Maintenance insights. 

## 2. System Contract Boundaries & Repositories

```
┌────────────────────────────────────────────────────────────────────────┐
│ MEMBER 1: BACKEND CORE (Me)                                             │
│ - FastAPI Engine - Dependency Injection - RBAC Policy Authorization    │
└──────────────────┬──────────────────────────────────┬──────────────────┘
                   │                                  │
                   ▼ (Repository Contracts)           ▼ (Service Adaptors)
┌──────────────────────────────────────┐  ┌──────────────────────────────┐
│ MEMBER 2: IIOT & REPO                │  │ MEMBER 3: AI & GRAPH         │
│ - TimescaleDB / PostgreSQL Storage   │  │ - Graph RAG Execution Engine │
│ - MQTT Data Broker & Simulator       │  │ - Predictive Health Models   │
└──────────────────────────────────────┘  └──────────────────────────────┘
```

## 3. Integration SLA Targets
- **Internal Cross-Module Bounds:** AsyncIO non-blocking interface execution.
- **Database Thread Isolation:** Member 2 schemas must expose bounded async repository abstractions to Member 1 to maintain core structural decoupling.