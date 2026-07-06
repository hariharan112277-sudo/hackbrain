# Backend Integration Handover Manual (Target: Member 1)

## 1. Programmatic Initialization Blueprint

```python
from uuid import UUID
from database.session import EnterpriseDBSessionScope
from database.repositories import MachineSQLRepository
from integration.registry import MachineRegistryService

def initialize_enterprise_registry_service() -> MachineRegistryService:
    concrete_machine_repository = MachineSQLRepository()
    allocated_registry_service = MachineRegistryService(machine_repo=concrete_machine_repository)
    return allocated_registry_service

def process_api_request_scope(target_machine_id: UUID) -> dict:
    service = initialize_enterprise_registry_service()
    with EnterpriseDBSessionScope() as active_session:
        machine_dto = service.get_machine(active_session, target_machine_id)
        return machine_dto.model_dump()
```

## 2. Concrete Verification Checklist
* [x] **Environment Integration:** Add all parameters from `handover/config/integration_env.example` into your local `.env` file profiles.
* [x] **Database Session Management:** Ensure your request router dependencies inject a read/write transaction context token compatible with SQLAlchemy's `Session` interface.
* [x] **Error Mapping Rules:** Wrap service integration calls in try/except blocks that intercept exceptions defined in `integration.exceptions` (e.g., `ResourceNotFoundError`), mapping them directly to appropriate HTTP status codes.
