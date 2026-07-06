# Cross-Functional Team Support Charter & Domain Boundary Governance

**Platform:** Industrial Operating Brain (IOB)  
**Document Owner:** Principal Industrial IoT Platform Owner  
**Standard Compliance:** Conway's Law & Domain-Driven Design Context Mapping

---

## 1. Governance Rule: Strict Ownership Boundaries

As Platform Owner, our responsibility is to provide robust, high-availability data infrastructure, clean contract abstractions, and architectural guidance. **We strictly DO NOT implement application business logic, AI/ML neural networks, or UI dashboard rendering code.**

```text
┌────────────────────────────────────────────────────────────────────────┐
│             PLATFORM OWNER & DATA ENGINEERING DOMAIN (Member 2)        │
│  • MQTT Fabric • TimescaleDB • Ingestion Pipeline • Service Interfaces │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ Immutable Contracts (DTOs & Schemas)
          ┌────────────────────────┼────────────────────────┐
          ▼                        ▼                        ▼
┌──────────────────┐    ┌────────────────────┐    ┌──────────────────┐
│ BACKEND (Member 1)│    │   AI/ML (Member 3) │    │FRONTEND (Member 4)│
│ • FastAPI Routes │    │ • Feature Training │    │ • Dashboard UX   │
│ • RBAC / Auth    │    │ • RUL Regression   │    │ • WebGL Charts   │
└──────────────────┘    └────────────────────┘    └──────────────────┘
```

---

## 2. Domain Support & Engagement Matrix

| Teams Supported | Provided Platform Artifacts & Guidance | Strict Exclusion (What We DO NOT Do) | Engagement Channel |
| :--- | :--- | :--- | :--- |
| **Backend Team (Member 1)** | Provide type-safe `interfaces.py` contracts, `EnterpriseDBSessionScope` transaction management, and connection pooling guidelines. | We do not write FastAPI controllers, JWT authentication filters, or API business route handlers. | Bi-weekly API Contract Triage & Architecture Review. |
| **AI / ML Team (Member 3)** | Provide automated Phase 7 CSV/JSON datasets (`historical.csv`), statistical profiling manifests, and RUL countdown targets. | We do not write PyTorch/TensorFlow training loops, feature selection models, or hyperparameter tuning scripts. | Data Hand-off Gate Review & Feature Dictionary updates. |
| **Frontend Team (Member 4)** | Provide machine state lifecycle definitions (`ONLINE`, `MAINTENANCE`, `OFFLINE`) and payload sizing limits ($<2\text{ KB}$). | We do not write React/Vue components, CSS stylesheets, or WebGL rendering canvases. | UI Contract Mapping & Cadence Triage. |
| **Operations / SRE Team** | Provide Docker Compose container deployments, Grafana/Prometheus alert rules, daily backup scripts, and disaster recovery runbooks. | We do not manage host OS kernel patches or physical datacenter server racks. | Monthly Operations & Maintenance Review. |
| **QA / Verification Team** | Provide automated 65-test verification suite, fault injection test cases (`FI-01` to `FI-04`), and JSON schema validators. | We do not perform manual exploratory testing or end-user acceptance sign-offs. | Continuous Integration Pipeline Gate. |
