# IOB Core Module Integration Contract Layer (Phase 6)

## Overview
This module defines the architectural interface boundaries for the Industrial Operating Brain (IOB). It provides strongly typed Data Transfer Objects (DTOs) and decoupled Service Interfaces that abstract the lower-level persistence and MQTT ingestion infrastructure.

**This module does not declare FastAPI routes, implement auth validation loops, or write raw database commits.** It serves as the single source of truth for programmatic contracts, ensuring seamless integration between development teams.

## Manual for Member 1 (Application System Architect Integration Guide)
1. **Dependency Injection Inversion Setups:**
   Bind the infrastructure-layer implementation handles developed in Phase 5 to the core abstract services constructors during your initialization sequences:
   ```python
   from integration.registry import MachineRegistryService
   from database.repositories import PostgresMachineRepositoryImplementation # Developed in Phase 5

   # Inject lower-level infrastructure dependencies into the decoupled registry service
   machine_registry_service = MachineRegistryService(machine_repo=PostgresMachineRepositoryImplementation())
   ```

2. **Controller Routing Implementation Reference Model:** Inject the configured abstractions directly into your controller functions, keeping your application logic isolated from low-level storage drivers:
   ```python
   @router.get("/api/v1/industrial/machines/{machine_id}", response_model=MachineDTO)
   def get_machine_registry_record(machine_id: UUID4, db_session = Depends(get_db_session)):
       try:
           return machine_registry_service.get_machine(db_session, machine_id)
       except ResourceNotFoundError as ex:
           raise HTTPException(status_code=404, detail=str(ex))
   ```

## Local Verification Testing Strategy
Execute the contract compliance and DTO validation test suite using the following command:
```bash
pytest integration/tests/test_contracts_and_services.py -vv
```

---

### Complete File Structure Layout Map

```text
integration/
├── README.md
├── interfaces.py
├── contracts.py
├── registry.py
├── mqtt_service.py
├── telemetry_service.py
├── asset_service.py
├── sensor_service.py
├── history_service.py
├── metadata_service.py
├── query_service.py
├── exceptions.py
├── logger.py
├── config.py
├── docs/
│   └── openapi_specs.yaml
├── examples/
│   └── backend_orchestration_sample.py
└── tests/
    └── test_contracts_and_services.py
```
