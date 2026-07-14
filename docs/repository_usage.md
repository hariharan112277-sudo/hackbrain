# Repository Usage Guide
## Phase 5: Member 2 Integration Patterns

### Overview

This guide documents how to implement and use the repository interfaces defined by Member 1. Member 2 provides the concrete implementations for PostgreSQL/TimescaleDB and MQTT integration.

### Repository Pattern

Each repository follows the **Repository Pattern** with async/await:

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class IRepository(ABC):
    @abstractmethod
    async def method_name(self, params) -> ReturnType:
        ...
```

### Machine Repository Implementation

#### Database Schema (PostgreSQL)
```sql
CREATE TABLE machines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    serial_number VARCHAR(100) UNIQUE NOT NULL,
    model VARCHAR(100),
    manufacturer VARCHAR(100),
    location VARCHAR(255),
    status VARCHAR(50) DEFAULT 'unknown',
    parent_id UUID REFERENCES machines(id),
    tags JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_machines_serial ON machines(serial_number);
CREATE INDEX idx_machines_status ON machines(status);
CREATE INDEX idx_machines_parent ON machines(parent_id);
```

#### Implementation Example
```python
# app/repositories/adapters/machine_repo.py
from app.repositories.interfaces import IMachineRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

class PostgresMachineRepository(IMachineRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def list_machines(self, filters=None, limit=100, offset=0):
        query = select(MachineModel)
        
        if filters:
            if filters.get("status"):
                query = query.where(MachineModel.status == filters["status"])
            if filters.get("search"):
                search = f"%{filters['search']}%"
                query = query.where(
                    MachineModel.name.ilike(search) | 
                    MachineModel.serial_number.ilike(search)
                )
        
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return [self._to_dict(m) for m in result.scalars()]
    
    async def get_by_id(self, machine_id):
        query = select(MachineModel).where(MachineModel.id == UUID(machine_id))
        result = await self.session.execute(query)
        machine = result.scalar_one_or_none()
        return self._to_dict(machine) if machine else None
    
    async def get_by_serial(self, serial_number):
        query = select(MachineModel).where(MachineModel.serial_number == serial_number)
        result = await self.session.execute(query)
        machine = result.scalar_one_or_none()
        return self._to_dict(machine) if machine else None
    
    async def create(self, machine_data):
        machine = MachineModel(**machine_data)
        self.session.add(machine)
        await self.session.commit()
        await self.session.refresh(machine)
        return self._to_dict(machine)
    
    async def update(self, machine_id, updates):
        machine = await self.get_by_id(machine_id)
        if not machine:
            return None
        for key, value in updates.items():
            setattr(machine, key, value)
        machine.updated_at = datetime.utcnow()
        await self.session.commit()
        return self._to_dict(machine)
    
    async def delete(self, machine_id):
        machine = await self.get_by_id(machine_id)
        if not machine:
            return False
        await self.session.delete(machine)
        await self.session.commit()
        return True
    
    async def get_machine_hierarchy(self, root_id):
        # Recursive CTE for hierarchy
        query = f"""
        WITH RECURSIVE hierarchy AS (
            SELECT * FROM machines WHERE id = '{root_id}'
            UNION ALL
            SELECT m.* FROM machines m
            INNER JOIN hierarchy h ON m.parent_id = h.id
        )
        SELECT * FROM hierarchy;
        """
        result = await self.session.execute(text(query))
        return {"root": root_id, "children": [self._to_dict(r) for r in result]}
    
    def _to_dict(self, model) -> Dict:
        return {
            "id": str(model.id),
            "name": model.name,
            "serial_number": model.serial_number,
            "model": model.model,
            "manufacturer": model.manufacturer,
            "location": model.location,
            "status": model.status,
            "parent_id": str(model.parent_id) if model.parent_id else None,
            "tags": model.tags,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None,
        }
```

### Telemetry Repository Implementation

#### Database Schema (TimescaleDB)
```sql
CREATE TABLE telemetry (
    time TIMESTAMPTZ NOT NULL,
    machine_id UUID NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit VARCHAR(50),
    quality VARCHAR(20) DEFAULT 'good',
    tags JSONB DEFAULT '{}'
);

SELECT create_hypertable('telemetry', 'time', chunk_time_interval => INTERVAL '1 day');

CREATE INDEX idx_telemetry_machine_time ON telemetry (machine_id, time DESC);
CREATE INDEX idx_telemetry_metric ON telemetry (metric_name);
```

#### Implementation Example
```python
# app/repositories/adapters/telemetry_repo.py
from app.repositories.interfaces import ITelemetryRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime
from typing import List, Dict, Any, Optional

class TimescaleTelemetryRepository(ITelemetryRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_latest_telemetry(self, machine_id) -> Optional[Dict]:
        query = text("""
            SELECT DISTINCT ON (metric_name) metric_name, value, unit, time as timestamp, quality
            FROM telemetry
            WHERE machine_id = :machine_id
            ORDER BY metric_name, time DESC
        """)
        result = await self.session.execute(query, {"machine_id": machine_id})
        metrics = [{"name": r.metric_name, "value": r.value, "unit": r.unit, 
                   "timestamp": r.timestamp.isoformat(), "quality": r.quality} 
                  for r in result]
        return {"machine_id": machine_id, "metrics": metrics, "timestamp": datetime.utcnow().isoformat()} if metrics else None
    
    async def get_telemetry_history(self, machine_id, start_time, end_time, 
                                     metrics=None, aggregation=None, interval=None) -> List[Dict]:
        # Build dynamic query based on aggregation
        if aggregation and interval:
            return await self._get_aggregated(machine_id, start_time, end_time, metrics, aggregation, interval)
        return await self._get_raw(machine_id, start_time, end_time, metrics)
    
    async def _get_raw(self, machine_id, start_time, end_time, metrics) -> List[Dict]:
        query = text("""
            SELECT time, metric_name, value, unit, quality
            FROM telemetry
            WHERE machine_id = :machine_id
            AND time BETWEEN :start AND :end
            """ + ("AND metric_name = ANY(:metrics)" if metrics else "") + """
            ORDER BY time DESC
        """)
        params = {"machine_id": machine_id, "start": start_time, "end": end_time}
        if metrics:
            params["metrics"] = metrics
        
        result = await self.session.execute(query, params)
        # Group by timestamp
        grouped = {}
        for row in result:
            ts = row.time.isoformat()
            if ts not in grouped:
                grouped[ts] = {"timestamp": ts, "metrics": []}
            grouped[ts]["metrics"].append({
                "name": row.metric_name, "value": row.value, 
                "unit": row.unit, "quality": row.quality
            })
        return list(grouped.values())
    
    async def _get_aggregated(self, machine_id, start_time, end_time, 
                               metrics, aggregation, interval) -> List[Dict]:
        agg_func = {"avg": "AVG", "min": "MIN", "max": "MAX", "sum": "SUM"}.get(aggregation, "AVG")
        query = text(f"""
            SELECT time_bucket(:interval, time) as bucket,
                   metric_name,
                   {agg_func}(value) as value,
                   MAX(unit) as unit
            FROM telemetry
            WHERE machine_id = :machine_id
            AND time BETWEEN :start AND :end
            """ + ("AND metric_name = ANY(:metrics)" if metrics else "") + """
            GROUP BY bucket, metric_name
            ORDER BY bucket
        """)
        params = {"machine_id": machine_id, "start": start_time, "end": end_time, 
                  "interval": interval}
        if metrics:
            params["metrics"] = metrics
        
        result = await self.session.execute(query, params)
        # Format response
        grouped = {}
        for row in result:
            ts = row.bucket.isoformat()
            if ts not in grouped:
                grouped[ts] = {"timestamp": ts, "metrics": []}
            grouped[ts]["metrics"].append({
                "name": row.metric_name, "value": float(row.value), "unit": row.unit
            })
        return list(grouped.values())
    
    async def get_telemetry_statistics(self, machine_id, start_time, end_time, metrics) -> Dict:
        query = text("""
            SELECT metric_name,
                   COUNT(*) as count,
                   MIN(value) as min_val,
                   MAX(value) as max_val,
                   AVG(value) as avg_val,
                   STDDEV(value) as std_val
            FROM telemetry
            WHERE machine_id = :machine_id
            AND time BETWEEN :start AND :end
            AND metric_name = ANY(:metrics)
            GROUP BY metric_name
        """)
        result = await self.session.execute(query, {
            "machine_id": machine_id, "start": start_time, "end": end_time, "metrics": metrics
        })
        return {row.metric_name: {
            "count": row.count, "min": row.min_val, "max": row.max_val,
            "avg": row.avg_val, "std": row.std_val
        } for row in result}
    
    async def insert_telemetry_batch(self, machine_id, readings) -> int:
        query = text("""
            INSERT INTO telemetry (time, machine_id, metric_name, value, unit, quality, tags)
            VALUES (:time, :machine_id, :metric_name, :value, :unit, :quality, :tags)
        """)
        for reading in readings:
            await self.session.execute(query, {
                "time": reading["timestamp"],
                "machine_id": machine_id,
                "metric_name": reading["name"],
                "value": reading["value"],
                "unit": reading.get("unit"),
                "quality": reading.get("quality", "good"),
                "tags": reading.get("tags", {}),
            })
        await self.session.commit()
        return len(readings)
    
    async def get_machines_with_recent_telemetry(self, since, limit=100) -> List[Dict]:
        query = text("""
            SELECT DISTINCT machine_id, MAX(time) as last_time
            FROM telemetry
            WHERE time > :since
            GROUP BY machine_id
            ORDER BY last_time DESC
            LIMIT :limit
        """)
        result = await self.session.execute(query, {"since": since, "limit": limit})
        return [{"machine_id": str(r.machine_id), "last_telemetry_at": r.last_time.isoformat()} for r in result]
```

### Alarm Repository Implementation

#### Database Schema
```sql
CREATE TABLE alarms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    machine_id UUID NOT NULL REFERENCES machines(id),
    alarm_code VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    source VARCHAR(100),
    acknowledged_by UUID,
    acknowledged_at TIMESTAMPTZ,
    resolved_by UUID,
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alarms_machine_status ON alarms (machine_id, status);
CREATE INDEX idx_alarms_severity ON alarms (severity);
CREATE INDEX idx_alarms_created ON alarms (created_at);
```

#### MQTT Listener Integration
```python
# app/repositories/adapters/mqtt_alarm_listener.py
import json
import asyncio
from app.core.dependencies import get_alarm_repo
from app.core.config import settings
import paho.mqtt.client as mqtt

class MQTTAlarmListener:
    def __init__(self):
        self.client = mqtt.Client(client_id=settings.MQTT_CLIENT_ID)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
    
    def _on_connect(self, client, userdata, flags, rc):
        client.subscribe("industrial/alarms/+")
    
    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            machine_id = msg.topic.split("/")[-1]
            
            alarm_data = {
                "machine_id": machine_id,
                "alarm_code": payload.get("code"),
                "message": payload.get("message"),
                "severity": payload.get("severity", "medium"),
                "source": payload.get("source", "mqtt"),
            }
            
            # Use alarm repository to create alarm
            alarm_repo = get_alarm_repo()
            asyncio.create_task(alarm_repo.create_alarm(alarm_data))
        except Exception as e:
            logger.error("mqtt_alarm_error", error=str(e))
    
    def start(self):
        self.client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT)
        self.client.loop_start()
    
    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
```

### Metadata Repository Implementation

#### Database Schema
```sql
CREATE TABLE machine_sensors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    machine_id UUID NOT NULL REFERENCES machines(id),
    sensor_id VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100),
    unit VARCHAR(50),
    location VARCHAR(255),
    sampling_rate DOUBLE PRECISION,
    range_min DOUBLE PRECISION,
    range_max DOUBLE PRECISION,
    UNIQUE(machine_id, sensor_id)
);

CREATE TABLE alarm_thresholds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    machine_id UUID NOT NULL REFERENCES machines(id),
    metric VARCHAR(100) NOT NULL,
    warning_low DOUBLE PRECISION,
    warning_high DOUBLE PRECISION,
    critical_low DOUBLE PRECISION,
    critical_high DOUBLE PRECISION,
    enabled BOOLEAN DEFAULT TRUE,
    UNIQUE(machine_id, metric)
);

CREATE TABLE maintenance_schedule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    machine_id UUID NOT NULL REFERENCES machines(id),
    task_name VARCHAR(255) NOT NULL,
    description TEXT,
    interval_days INTEGER,
    last_performed TIMESTAMPTZ,
    next_due TIMESTAMPTZ,
    assigned_to UUID
);
```

### Dependency Injection Setup

In your application startup:

```python
# main.py or startup.py
from app.core.dependencies import set_repositories
from app.repositories.adapters import (
    PostgresMachineRepository,
    TimescaleTelemetryRepository,
    PostgresAlarmRepository,
    PostgresMetadataRepository,
    PostgresUserRepository,
    PostgresRoleRepository,
    PostgresPermissionRepository,
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Create database engine
engine = create_async_engine(settings.DATABASE_URL, pool_size=20, max_overflow=10)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session

# Initialize repositories with DB session
async def init_repositories():
    async with async_session() as session:
        set_repositories(
            machine_repo=PostgresMachineRepository(session),
            telemetry_repo=TimescaleTelemetryRepository(session),
            alarm_repo=PostgresAlarmRepository(session),
            metadata_repo=PostgresMetadataRepository(session),
            user_repo=PostgresUserRepository(session),
            role_repo=PostgresRoleRepository(session),
            permission_repo=PostgresPermissionRepository(session),
        )

# Start MQTT listener
from app.repositories.adapters.mqtt_alarm_listener import MQTTAlarmListener
mqtt_listener = MQTTAlarmListener()
mqtt_listener.start()
```

### Testing Repository Implementations

```python
# tests/test_repositories.py
import pytest
from app.repositories.interfaces import IMachineRepository

@pytest.mark.asyncio
async def test_machine_repository_contract(machine_repo: IMachineRepository):
    """Test that implementation satisfies interface contract."""
    # Create
    machine = await machine_repo.create({
        "name": "Test Machine",
        "serial_number": "TEST-001",
        "status": "online",
    })
    assert machine["id"] is not None
    
    # Get by ID
    retrieved = await machine_repo.get_by_id(machine["id"])
    assert retrieved["serial_number"] == "TEST-001"
    
    # Get by Serial
    by_serial = await machine_repo.get_by_serial("TEST-001")
    assert by_serial["id"] == machine["id"]
    
    # Update
    updated = await machine_repo.update(machine["id"], {"status": "maintenance"})
    assert updated["status"] == "maintenance"
    
    # List
    machines, total = await machine_repo.list_users(limit=10)
    assert total >= 1
    
    # Delete
    deleted = await machine_repo.delete(machine["id"])
    assert deleted is True
```