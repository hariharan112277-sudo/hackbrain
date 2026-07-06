# Platform Change Management Registry & Feature Evaluation Framework

**Platform:** Industrial Operating Brain (IOB)  
**Document Owner:** Principal Industrial IoT Platform Owner  
**Lifecycle Stage:** Post-Version 1.0 Production Evaluation

---

## 1. Feature Evaluation & Categorization Framework

Incoming feature requests, infrastructure upgrades, and defect reports are rigorously evaluated by the Platform Owner and assigned to explicit change categories:
* **Critical Bug:** Production defect causing SLA breach, data loss, or security vulnerability. Targeted for patch release (`v1.0.X`).
* **Minor Bug:** Non-service-impacting edge case or logging error. Targeted for maintenance patch (`v1.0.X`).
* **Feature Request:** Downstream consumer capability expansion without breaking contracts. Targeted for minor release (`v1.X.0`).
* **Architecture Change:** Structural shift in messaging or storage engines (e.g., Kafka introduction). Targeted for major release (`v2.0.0`).
* **Performance Improvement:** Internal indexing or connection pooling optimization. Targeted for minor release (`v1.X.0`).
* **Infrastructure / Version Upgrade:** OS, Docker, Python, or database engine upgrade. Targeted for minor or major release depending on breaking changes.

---

## 2. Active Change Management Board (CCB Registry)

| Change ID | Request Title | Category | Priority | Risk | Effort | Dependencies | Target Release | CCB Approval Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CHG-2026-001** | Implement Native OPC-UA Hardware Connectors | Feature Request | P1 - High | Medium | 8 Weeks | Edge Hardware Gateways | **Version 1.1.0** | **APPROVED** |
| **CHG-2026-002** | Add Connection Pool Multiplexing via PgBouncer | Performance Improvement | P2 - Medium | Low | 2 Weeks | TimescaleDB Cluster | **Version 1.1.0** | **APPROVED** |
| **CHG-2026-003** | Migrate Single-Threaded Subscriber to Apache Kafka Bus | Architecture Change | P1 - High | High | 12 Weeks | Kafka Cluster Deployment | **Version 2.0.0** | **APPROVED** |
| **CHG-2026-004** | Real-Time Interactive Digital Twin 3D Asset Synchronization | Feature Request | P2 - Medium | High | 16 Weeks | Phase 6 Integration DTOs | **Version 3.0.0** | **EVALUATING** |
| **CHG-2026-005** | Enforce mTLS 1.3 Client Certificate Authentication on EMQX | Infrastructure Upgrade | P1 - High | Low | 3 Weeks | PKI Certificate Authority | **Version 1.2.0** | **APPROVED** |
