# Strategic Engineering Roadmap: IOB Version 2.0

**Platform:** Industrial Operating Brain (IOB)  
**Target Release Window:** Q1 2027 (Months 4 — 6)  
**Document Owner:** Principal Industrial IoT Platform Owner

---

## 1. Executive Summary & V2.0 Strategic Goals
While Version 1.0 established a rock-solid data foundation using simulated MQTT feeds and single-node processing, **Version 2.0 transforms the Industrial Operating Brain into a distributed, multi-protocol enterprise fabric.** Version 2.0 focuses on real-world shop-floor PLC integration, highly scalable Apache Kafka event streaming, and cloud synchronization across multi-site factory hubs.

---

## 2. Version 2.0 Architecture & Feature Specifications

### 2.1 Physical Shop-Floor PLC & Protocol Connectivity
* **Native PLC Integration:** Direct driver communication with **Siemens S7-1500 / S7-1200** (via PROFINET / S7 Comm) and **Rockwell Allen-Bradley ControlLogix** (via EtherNet/IP).
* **Fieldbus Protocols:** Native polling loops for **Modbus TCP** and ruggedized serial **Modbus RTU** gateways.
* **Industrial Interoperability:** Embedded **OPC-UA Client Connectors** and **MQTT Sparkplug B** edge gateways ensuring standardized payload self-description and birth/death certificates (`NBIRTH`, `NDEATH`).

### 2.2 Distributed Ingestion Backbone (Apache Kafka & Industrial Cloud Hubs)
* **Event Streaming Architecture:** Replace single-process Python subscribers with a high-throughput **Apache Kafka Cluster** partitioned by `machine_id`. Scales ingestion throughput past **10,000+ messages/sec** without CPU starvation.
* **Hybrid Cloud Sync:** Bi-directional synchronization bridges connecting edge TimescaleDB instances to **Azure IoT Hub**, **AWS IoT Core**, and **Google Cloud IoT**.
* **Enterprise IT/OT Convergence:** Native bi-directional integration adapters for **SCADA** monitoring engines, Manufacturing Execution Systems (**MES**), and Enterprise Resource Planning (**ERP** — SAP S/4HANA).

---

## 3. Version 2.0 Execution Blueprint

| Assessment Dimension | Strategic Evaluation & Engineering Parameters |
| :--- | :--- |
| **Technical Feasibility** | **High.** All required industrial protocols (OPC-UA, Sparkplug B, Kafka) have mature open-source C/C++/Python libraries (`asyncua`, `confluent-kafka`). |
| **Architecture Impact** | **Medium.** Phase 6 interfaces (`IMQTTIntegrationService`, `ITelemetryRepository`) remain 100% stable for Member 1. Internal ingestion worker loop (`pipeline.py`) adapts to pull from Kafka topics instead of memory queues. |
| **Migration Strategy** | **Zero-Downtime Dual-Ingestion:** Deploy Kafka cluster in parallel with EMQX broker. Edge gateways dual-publish to MQTT and Kafka during a 30-day verification window before sunsetting direct MQTT subscriber workers. |
| **Estimated Timeline** | **16 Weeks** (4 weeks edge driver development $\rightarrow$ 6 weeks Kafka cluster deployment $\rightarrow$ 4 weeks MES/ERP adapters $\rightarrow$ 2 weeks E2E validation). |
| **Engineering Risks** | Network jitter over serial Modbus RTU lines causing read timeouts; Kafka partition rebalancing delays during node failures. |
