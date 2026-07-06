# Enterprise Incident Management & History Registry

**Platform:** Industrial Operating Brain (IOB)  
**Document Owner:** Principal Industrial IoT Platform Owner  
**Standard Compliance:** ITIL Service Operation & ISO/IEC 20000

---

## 1. Incident Classification & Severity Matrix

To ensure clear operational governance, all incidents impacting the Industrial Operating Brain are categorized according to severity, response SLAs, and escalation pathways:

| Severity Level | Definition & Operational Impact | Response SLA | Resolution Target | Escalation Protocol |
| :--- | :--- | :--- | :--- | :--- |
| **SEV-1 (Critical)** | Complete loss of MQTT ingestion backbone or database core; $\ge 25\%$ data drop rate across plant floor. | $< 5$ Minutes | $< 30$ Minutes | Immediate paging of Platform Owner, Lead SRE, and VP of Operations. |
| **SEV-2 (High)** | Single production line telemetry loss; processing latency $> 500\text{ms}$; DLQ rejection rate $> 5\%/\text{min}$. | $< 15$ Minutes | $< 2$ Hours | Page Lead Core Engineer and On-Call DevOps Support. |
| **SEV-3 (Medium)** | Non-critical historical query timeouts; AI dataset generation delays; localized redundant sensor dropout. | $< 1$ Hour | $< 12$ Hours | Assign ticket to Level 1 SRE / Operations queue. |
| **SEV-4 (Low)** | Minor configuration drift warnings; non-service-impacting log warnings; documentation typos. | $< 24$ Hours | Scheduled Sprint | Backlog item reviewed during bi-weekly platform triage. |

---

## 2. Standard Incident Report Template

Every recorded incident must maintain a structured document record:

```markdown
### Incident Report: [INC-YYYYMMDD-00X] — [Title]

**Incident Status:** Resolved / Closed  
**Severity:** SEV-1 / SEV-2 / SEV-3  
**Detection Time (UTC):** YYYY-MM-DDTHH:MM:SSZ  
**Resolution Time (UTC):** YYYY-MM-DDTHH:MM:SSZ  
**Total Outage Duration:** XX Minutes  

#### 1. Impact Analysis
* **Affected Components:** [e.g., EMQX Broker Node 2, MQTT Subscriber Worker Pool]
* **Operational Impact:** [e.g., 4,500 telemetry packets buffered at edge gateways; 0 permanent packet loss due to QoS 1 backoff buffer].

#### 2. Chronological Timeline
* `T-00:00` — High memory alarm triggered on `iob-ingestion-subscriber`.
* `T+00:05` — On-Call engineer acknowledged page; initiated container triage.
* `T+00:12` — Discovered unhandled garbage collection pause during 10,000 msg/sec load burst.
* `T+00:18` — Applied hotfix scaling container memory limits and restarted consumer workers.

#### 3. Root Cause Analysis
Detailed technical explanation of structural failure mechanisms.

#### 4. Action Items & Lessons Learned
* **Action Item 1:** Implement automated memory threshold pre-scaling alerts at 75% capacity.
* **Action Item 2:** Review Python object recycling inside `SlidingWindowDuplicateDetector`.
```

---

## 3. Historical Production Incident Registry (Post-Version 1.0 Release)

| Incident ID | Date | Severity | Affected Components | Root Cause Summary | Status | CAPA Reference |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **INC-20260703-001** | 2026-07-03 | SEV-2 | `cleaner.py` Z-Score Engine | Median Absolute Deviation (`MAD`) returned `NaN` when OPC quality code 64 introduced null values into sliding array, causing outlier filter skip. | **CLOSED** | Patched via `np.nanmedian(...)` and verified in V1.0 regression suite. |
| **INC-20260703-002** | 2026-07-03 | SEV-3 | `test_system_handover` | Pydantic V2 DTO validation failed when ORM `Machine` object lacked explicit `status` property during direct repository mapping. | **CLOSED** | Added `@property` encapsulation on ORM `Machine` entity. |
