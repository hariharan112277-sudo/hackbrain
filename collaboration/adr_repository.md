# Architecture Decision Record (ADR) Repository & Technical Standards

**Platform:** Industrial Operating Brain (IOB)  
**Document Owner:** Principal Industrial IoT Platform Owner

---

## 1. Architecture Decision Records (ADRs)

### ADR-001: Adoption of Repository Pattern for Data Access
* **Status:** Accepted (Version 1.0)
* **Context:** Member 1 FastAPI endpoints required access to database tables without coupling application logic to raw SQL or SQLAlchemy ORM sessions.
* **Decision:** Implement generic `IBaseCRUD[T]` and domain repositories (`IMachineRepository`, `MachineSQLRepository`) that return frozen Pydantic V2 DTOs (`MachineDTO`).
* **Consequences:** (+) Complete isolation of DB schemas; (+) Easy mocking in unit tests. (-) Requires mapping overhead via `EntityDTOMapper`.

### ADR-002: TimescaleDB Hypertables over Vanilla PostgreSQL
* **Status:** Accepted (Version 1.0)
* **Context:** High-frequency telemetry streams ($1,000+$ msg/sec) cause rapid table bloat and B-tree index degradation in standard PostgreSQL tables.
* **Decision:** Utilize TimescaleDB extension partitioned by 7-day time intervals (`PARTITION BY RANGE (timestamp)`).
* **Consequences:** (+) $10\times$ faster insertion rates; (+) Automatic compression of older chunks. (-) Requires TimescaleDB-specific Docker container.

### ADR-003: Modified Z-Score over Standard Z-Score for Outlier Scrubbing
* **Status:** Accepted (Version 1.0)
* **Context:** Industrial sensor noise and mechanical shock cause extreme spikes ($> 500\text{ mm/s}$) that distort standard mean and variance calculations during data cleaning.
* **Decision:** Utilize Median Absolute Deviation (`MAD`) inside `IndustrialDataCleaner` (`modified_z = 0.6745 * (vals - median) / mad`).
* **Consequences:** (+) Robust outlier detection immune to extreme spikes. (-) Requires `np.nanmedian` defense against null arrays.

---

## 2. Technical & Coding Standards

* **Industrial Standards:** All physical asset modeling must adhere to **ISA-95 Part 2** equipment hierarchy. Operational modes must adhere to **ISA-88** batch states.
* **Python Coding Standards:** All modules must enforce PEP 8 formatting, explicit type annotations (`typing.Optional`, `typing.Dict`), and Pydantic V2 strict validation (`ConfigDict(frozen=True)`).
* **Documentation Standards:** Every public class and method must include docstrings detailing industrial standard compliance, expected exceptions, and parameters.
