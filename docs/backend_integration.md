# Backend Integration Guide
## Phase 5: Member 1 - Industrial Operating Brain (IOB)

### Overview

This document describes the backend integration architecture for Phase 5 of the IOB platform. Member 1 is responsible for the central orchestration layer that connects:

- **Member 2 (IoT & Database)**: Repository layer implementations
- **Member 3 (AI Subsystem)**: Anomaly detection and RUL prediction services
- **Member 4 (Frontend/UI)**: Dashboard and real-time data APIs

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        IOB Backend (Member 1)                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   API       │  │  Service    │  │ Repository  │             │
│  │  Layer      │──│  Layer      │──│  Interfaces │             │
│  └─────────────┘  └─────────────┘  └──────┬──────┘             │
│                                            │                    │
│                    ┌───────────────────────┼───────────────┐   │
│                    │                       ▼               │   │
│                    │  ┌─────────────────────────────────┐  │   │
│                    │  │     Member 2 Implementation     │  │   │
│                    │  │  (PostgreSQL, TimescaleDB, MQTT)│  │   │
│                    │  └─────────────────────────────────┘  │   │
│                    │                                       │   │
│                    │  ┌─────────────────────────────────┐  │   │
│                    │  │     Member 3 AI Services        │  │   │
│                    │  │  (Anomaly Detection, RUL Pred)  │  │   │
│                    │  └─────────────────────────────────┘  │   │
│                    └───────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Repository Interface Contracts

Member 1 defines abstract interfaces in `app/repositories/interfaces.py` that Member 2 must implement:

#### IMachineRepository
```python
async def list_machines(filters, limit, offset) -> List[Dict]
async def get_by_id(machine_id) -> Optional[Dict]
async def get_by_serial(serial_number) -> Optional[Dict]
async def create(machine_data) -> Dict
async def update(machine_id, updates) -> Dict
async def delete(machine_id) -> bool
async def get_machine_hierarchy(root_id) -> Dict
```

#### ITelemetryRepository
```python
async def get_latest_telemetry(machine_id) -> Optional[Dict]
async def get_telemetry_history(machine_id, start, end, metrics, aggregation, interval) -> List[Dict]
async def get_telemetry_statistics(machine_id, start, end, metrics) -> Dict
async def insert_telemetry_batch(machine_id, readings) -> int
async def get_machines_with_recent_telemetry(since, limit) -> List[Dict]
```

#### IAlarmRepository
```python
async def get_active_alarms(severity, machine_id, limit, offset) -> List[Dict]
async def get_alarm_history(machine_id, start, end, status, limit, offset) -> List[Dict]
async def get_alarm_by_id(alarm_id) -> Optional[Dict]
async def acknowledge_alarm(alarm_id, user_id, notes) -> Dict
async def resolve_alarm(alarm_id, user_id, resolution_notes) -> Dict
async def get_alarm_statistics(start, end, group_by) -> Dict
async def create_alarm(alarm_data) -> Dict  # Called by MQTT listener
```

#### IMetadataRepository
```python
async def get_machine_metadata(machine_id) -> Optional[Dict]
async def get_machine_sensors(machine_id) -> List[Dict]
async def get_thresholds(machine_id) -> Dict
async def update_thresholds(machine_id, thresholds) -> Dict
async def get_maintenance_schedule(machine_id) -> List[Dict]
async def get_firmware_version(machine_id) -> Optional[str]
async def get_machine_documentation(machine_id) -> List[Dict]
```

### Service Layer Orchestration

The service layer (`app/services/`) acts as the absolute orchestrator:

1. **IndustrialService** - Core industrial business logic
2. **DashboardService** - Aggregates data for UI components
3. **AuthService** - Authentication and token management
4. **UserService** - User and RBAC management

### API Contracts

All API endpoints use Pydantic schemas for request/response validation:

#### Machine Endpoints
- `GET /api/v1/industrial/machines` - List machines (paginated)
- `GET /api/v1/industrial/machines/{id}` - Get machine
- `POST /api/v1/industrial/machines` - Create machine
- `PATCH /api/v1/industrial/machines/{id}` - Update machine
- `DELETE /api/v1/industrial/machines/{id}` - Delete machine
- `GET /api/v1/industrial/machines/{id}/telemetry/flow` - Combined machine + telemetry + metadata

#### Telemetry Endpoints
- `GET /api/v1/industrial/machines/{id}/telemetry` - Latest telemetry
- `POST /api/v1/industrial/machines/{id}/telemetry/history` - Historical data
- `GET /api/v1/industrial/machines/{id}/telemetry/statistics` - Statistical summaries

#### Alarm Endpoints
- `GET /api/v1/industrial/alarms` - Active alarms
- `GET /api/v1/industrial/alarms/history` - Alarm history
- `POST /api/v1/industrial/alarms/{id}/acknowledge` - Acknowledge
- `POST /api/v1/industrial/alarms/{id}/resolve` - Resolve

#### AI Integration Stubs (Member 3)
- `POST /api/v1/industrial/ai/anomaly/predict` - Anomaly detection
- `POST /api/v1/industrial/ai/rul/predict` - RUL prediction

#### Dashboard Endpoints (Member 4)
- `GET /api/v1/dashboard/overview` - Complete dashboard
- `GET /api/v1/dashboard/machines/{id}/detail` - Machine detail
- `GET /api/v1/dashboard/kpis` - KPI widgets
- `GET /api/v1/dashboard/alarms/summary` - Alarm summary
- `GET /api/v1/dashboard/telemetry/widgets` - Telemetry widgets

### Integration Steps for Member 2

1. **Implement Repository Interfaces**
   ```python
   # Member 2 creates implementations
   from app.repositories.interfaces import IMachineRepository
   
   class PostgresMachineRepository(IMachineRepository):
       async def list_machines(self, filters, limit, offset):
           # Your PostgreSQL/TimescaleDB implementation
           ...
   ```

2. **Register Implementations at Startup**
   ```python
   # In your main.py or startup script
   from app.core.dependencies import set_repositories
   from your_implementations import (
       PostgresMachineRepository,
       TimescaleTelemetryRepository,
       PostgresAlarmRepository,
       PostgresMetadataRepository,
       PostgresUserRepository,
       PostgresRoleRepository,
       PostgresPermissionRepository,
   )
   
   set_repositories(
       machine_repo=PostgresMachineRepository(),
       telemetry_repo=TimescaleTelemetryRepository(),
       alarm_repo=PostgresAlarmRepository(),
       metadata_repo=PostgresMetadataRepository(),
       user_repo=PostgresUserRepository(),
       role_repo=PostgresRoleRepository(),
       permission_repo=PostgresPermissionRepository(),
   )
   ```

3. **MQTT Listener Integration**
   ```python
   # Member 2's MQTT listener creates alarms
   from app.core.dependencies import get_alarm_repo
   
   async def on_mqtt_message(topic, payload):
       alarm_repo = get_alarm_repo()
       await alarm_repo.create_alarm({
           "machine_id": payload["machine_id"],
           "alarm_code": payload["code"],
           "message": payload["message"],
           "severity": payload["severity"],
           "source": payload["source"],
       })
   ```

### Integration Steps for Member 3

1. **Replace AI Stubs in IndustrialService**
   ```python
   # In app/services/industrial_service.py
   async def predict_anomaly(self, request: AnomalyPredictionRequest):
       # Replace stub with actual AI service call
       response = await self._call_ai_service(
           endpoint=settings.AI_ANOMALY_ENDPOINT,
           data=request.model_dump(),
       )
       return AnomalyPredictionResponse(**response)
   
   async def predict_rul(self, request: RULPredictionRequest):
       response = await self._call_ai_service(
           endpoint=settings.AI_RUL_ENDPOINT,
           data=request.model_dump(),
       )
       return RULPredictionResponse(**response)
   ```

2. **Configure AI Service URLs**
   ```env
   AI_SERVICE_URL=http://ai-service:8001
   AI_ANOMALY_ENDPOINT=/predict/anomaly
   AI_RUL_ENDPOINT=/predict/rul
   ```

### Integration Steps for Member 4

1. **Use Defined API Contracts**
   All endpoints return strictly typed JSON matching Pydantic schemas in `app/schemas/`.

2. **Dashboard Data Structure**
   ```typescript
   // Example TypeScript interfaces (auto-generated from OpenAPI)
   interface DashboardOverview {
     machine_status: MachineStatusSummary;
     telemetry_widgets: TelemetryWidgetData[];
     alarm_widget: AlarmWidgetData;
     kpi_widgets: KPIWidgetData[];
     trend_widgets: TrendWidgetData[];
   }
   ```

3. **Real-time Updates**
   WebSocket endpoint at `/api/v1/dashboard/ws/telemetry` (placeholder in Phase 5)

### Testing Integration

Run integration tests:
```bash
pytest tests/test_integration.py -v
pytest tests/test_contracts.py -v
```

### Configuration

Key environment variables for integration:
```env
# Database (Member 2)
DATABASE_URL=postgresql://user:pass@host:5432/iob

# Redis
REDIS_URL=redis://localhost:6379/0

# MQTT (Member 2)
MQTT_BROKER_HOST=mqtt-broker
MQTT_BROKER_PORT=1883

# AI Service (Member 3)
AI_SERVICE_URL=http://ai-service:8001
ENABLE_AI_INTEGRATION=true

# Frontend (Member 4)
FRONTEND_URL=http://frontend:3000
CORS_ORIGINS=http://frontend:3000,http://localhost:3000
```