# Enterprise Security & Compliance Governance Framework

**Platform:** Industrial Operating Brain (IOB)  
**Document Owner:** Principal Industrial IoT Platform Owner  
**Standard Compliance:** IEC 62443 Industrial Cyber Security & Zero-Trust Architecture

---

## 1. IEC 62443 Security Audit & Defense Depth

To protect critical manufacturing assets from cyber-physical threats, the Industrial Operating Brain enforces a defense-in-depth Zero-Trust security posture across all operational zones:

| Security Domain | Operational Mechanism | IEC 62443 Security Level (SL) | Current Status & Audit Finding | Planned Future Enhancement |
| :--- | :--- | :--- | :--- | :--- |
| **MQTT Authentication & Encryption** | SCRAM-SHA-256 password hashing via EMQX internal ACL; TLS 1.3 encryption on Port 8883. | **SL-3** | Port 1883 open during local developer testing. | Enforce mutual TLS (mTLS X.509 client certificates) across all hardware gateways in V1.2. |
| **Network Segmentation (Purdue Model)** | Shop floor devices isolated in Purdue Level 0/1 VLANs; database restricted to Level 3 Enterprise zone. | **SL-3** | `pg_hba_production_rules.conf` restricts DB connections to internal subnets (`10.142.0.0/16`). | Implement Calico network policies enforcing micro-segmentation between containers. |
| **Database Encryption & Data at Rest** | AES-256 full disk volume encryption (`LUKS`) on TimescaleDB physical NVMe volumes. | **SL-3** | Verified active on production storage nodes. | Enable transparent table-level column encryption for sensitive asset metadata fields. |
| **Secrets & Credential Management** | Credentials injected via Docker environment profiles (`${IOB_DATABASE_SECURE_PASSWORD}`). | **SL-2** | Environment files excluded from git snapshots via `.gitignore`. | Integrate HashiCorp Vault dynamic secret generation with automated 30-day rotation. |
| **Role-Based Access Control (RBAC)** | Member 1 API layer enforces JWT/RBAC middleware before invoking Phase 6 integration services. | **SL-3** | Read-only database users provisioned for analytics queries (`iob_readonly`). | Implement fine-grained row-level security (RLS) inside TimescaleDB by factory site ID. |
