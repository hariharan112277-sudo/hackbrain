# Performance Optimization Guide
## Phase 5: Scalability, Caching, and Monitoring

### Overview

This document describes performance optimization strategies implemented in Phase 5 for the IOB platform, targeting high-throughput industrial IoT workloads.

### Database Optimization

#### Connection Pooling
```python
# app/core/config.py
DATABASE_POOL_SIZE: int = 20
DATABASE_MAX_OVERFLOW: int = 10
DATABASE_POOL_TIMEOUT: int = 30

# SQLAlchemy engine
engine = create_async_engine(
    DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_pre_ping=True,  # Validate connections
)
```

#### Query Optimization

**Indexes for Common Queries**
```sql
-- Machines
CREATE INDEX idx_machines_status ON machines(status);
CREATE INDEX idx_machines_parent ON machines(parent_id);
CREATE INDEX idx_machines_created ON machines(created_at);

-- Telemetry (TimescaleDB)
CREATE INDEX idx_telemetry_machine_time ON telemetry (machine_id, time DESC);
CREATE INDEX idx_telemetry_metric_time ON telemetry (metric_name, time DESC);

-- Alarms
CREATE INDEX idx_alarms_machine_status ON alarms (machine_id, status);
CREATE INDEX idx_alarms_severity_created ON alarms (severity, created_at);
```

**Async Query Patterns**
```python
# Use async/await for all DB operations
async def get_machines_with_telemetry(self, machine_ids: List[UUID]) -> List[Dict]:
    # Single query with JOIN instead of N+1 queries
    query = text("""
        SELECT m.*, 
               json_agg(json_build_object(
                   'name', t.metric_name,
                   'value', t.value,
                   'unit', t.unit,
                   'timestamp', t.time
               )) as telemetry
        FROM machines m
        LEFT JOIN LATERAL (
            SELECT DISTINCT ON (metric_name) metric_name, value, unit, time
            FROM telemetry
            WHERE machine_id = m.id
            ORDER BY metric_name, time DESC
        ) t ON true
        WHERE m.id = ANY(:machine_ids)
        GROUP BY m.id
    """)
    result = await self.session.execute(query, {"machine_ids": [str(m) for m in machine_ids]})
    return [self._to_dict(row) for row in result]
```

### Caching Strategy

#### Redis Caching
```python
# app/core/cache.py
import redis.asyncio as redis
from app.core.config import settings

redis_client = redis.from_url(
    settings.REDIS_URL,
    max_connections=settings.REDIS_MAX_CONNECTIONS,
    socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
    decode_responses=True,
)

async def get_cached(key: str) -> Optional[str]:
    return await redis_client.get(key)

async def set_cached(key: str, value: str, ttl: int = 300):
    await redis_client.setex(key, ttl, value)

async def invalidate_pattern(pattern: str):
    cursor = 0
    while True:
        cursor, keys = await redis_client.scan(cursor, match=pattern, count=100)
        if keys:
            await redis_client.delete(*keys)
        if cursor == 0:
            break
```

#### Cache TTL Strategy
| Data Type | TTL | Invalidation |
|-----------|-----|--------------|
| Machine list | 60s | On create/update/delete |
| Machine detail | 30s | On update |
| Latest telemetry | 10s | On new telemetry |
| Alarm counts | 30s | On alarm create/ack/resolve |
| Dashboard overview | 30s | Composite invalidation |
| User permissions | 300s | On role/permission change |

#### Cached Service Methods
```python
# app/services/industrial_service.py
class IndustrialService:
    async def get_all_machines(self, filters=None, limit=100, offset=0):
        cache_key = f"machines:list:{hash(str(filters))}:{limit}:{offset}"
        cached = await get_cached(cache_key)
        if cached:
            return json.loads(cached)
        
        result = await self.machine_repo.list_machines(filters, limit, offset)
        await set_cached(cache_key, json.dumps(result), ttl=60)
        return result
    
    async def create_machine(self, machine_data):
        result = await self.machine_repo.create(machine_data)
        await invalidate_pattern("machines:list:*")
        return result
```

### Async Processing

#### Background Tasks
```python
# FastAPI background tasks
from fastapi import BackgroundTasks

@router.post("/machines/{machine_id}/telemetry/batch")
async def insert_telemetry_batch(
    machine_id: UUID,
    readings: List[TelemetryReading],
    background_tasks: BackgroundTasks,
):
    # Immediate response
    background_tasks.add_task(
        telemetry_repo.insert_telemetry_batch,
        machine_id=machine_id,
        readings=readings,
    )
    return {"status": "accepted", "count": len(readings)}
```

#### Task Queue (Celery/Redis)
```python
# For heavy AI predictions
from celery import Celery

celery_app = Celery("iob_tasks", broker=settings.REDIS_URL)

@celery_app.task
def predict_anomaly_task(machine_id: str, telemetry_window: list):
    # Heavy ML inference
    return ai_service.predict_anomaly(machine_id, telemetry_window)

# In service
async def predict_anomaly(self, request):
    # Quick response, async processing
    task = predict_anomaly_task.delay(str(request.machine_id), request.telemetry_window)
    return {"task_id": task.id, "status": "processing"}
```

### Pagination Optimization

#### Keyset Pagination (Cursor-based)
```python
# For large datasets, use keyset pagination instead of OFFSET
async def list_machines_keyset(
    self,
    cursor: Optional[str] = None,
    limit: int = 100,
    filters: Dict = None,
) -> Dict:
    query = select(MachineModel).limit(limit + 1)
    
    if cursor:
        # Decode cursor (base64 encoded last seen ID)
        last_id = base64.b64decode(cursor).decode()
        query = query.where(MachineModel.id > UUID(last_id))
    
    if filters:
        query = self._apply_filters(query, filters)
    
    result = await self.session.execute(query)
    machines = [self._to_dict(m) for m in result.scalars()]
    
    has_more = len(machines) > limit
    if has_more:
        machines = machines[:limit]
    
    next_cursor = None
    if has_more and machines:
        next_cursor = base64.b64encode(str(machines[-1]["id"]).encode()).decode()
    
    return {"machines": machines, "next_cursor": next_cursor, "has_more": has_more}
```

### Monitoring & Metrics

#### Prometheus Metrics
```python
# app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Request metrics
REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", 
                       ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "Request latency",
                           ["method", "endpoint"])

# Business metrics
MACHINES_ONLINE = Gauge("machines_online", "Number of online machines")
ACTIVE_ALARMS = Gauge("active_alarms_total", "Total active alarms", ["severity"])
TELEMETRY_INGEST_RATE = Counter("telemetry_ingest_total", "Telemetry points ingested")

# Middleware
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

#### Health Checks with Dependencies
```python
@app.get("/health")
async def health_check():
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "mqtt": await check_mqtt(),
        "ai_service": await check_ai_service(),
    }
    
    healthy = all(checks.values())
    status_code = 200 if healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if healthy else "degraded",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )

async def check_database() -> bool:
    try:
        await db_session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
```

### Load Testing

#### Locust Test Script
```python
# tests/load_test.py
from locust import HttpUser, task, between

class IOBUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "SecurePass123!",
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def get_dashboard(self):
        self.client.get("/api/v1/dashboard/overview", headers=self.headers)
    
    @task(2)
    def list_machines(self):
        self.client.get("/api/v1/industrial/machines", headers=self.headers)
    
    @task(1)
    def get_telemetry(self):
        self.client.get("/api/v1/industrial/machines/machine-id/telemetry", 
                       headers=self.headers)

# Run: locust -f tests/load_test.py --host=http://localhost:8000
```

### Performance Benchmarks

| Endpoint | Target P95 | Target Throughput |
|----------|------------|-------------------|
| GET /health | < 10ms | 10,000 RPS |
| GET /machines (paginated) | < 100ms | 1,000 RPS |
| GET /machines/{id}/telemetry | < 50ms | 2,000 RPS |
| POST /telemetry/batch | < 200ms | 500 RPS |
| GET /dashboard/overview | < 200ms | 500 RPS |
| POST /ai/anomaly/predict | < 500ms | 100 RPS |

### Scaling Strategies

#### Horizontal Scaling
- Stateless API pods behind load balancer
- Shared Redis for caching/sessions
- Database read replicas for read-heavy workloads
- MQTT broker clustering (EMQX, VerneMQ)

#### Vertical Scaling
- Increase `DATABASE_POOL_SIZE` with CPU cores
- Increase `REDIS_MAX_CONNECTIONS`
- Add more gunicorn workers: `workers = 2 * CPU + 1`

#### Database Scaling
```sql
-- Partition telemetry by time (TimescaleDB handles automatically)
-- For massive scale, consider:
-- 1. TimescaleDB multi-node
-- 2. Separate telemetry database
-- 3. Data tiering (hot/warm/cold storage)
```

### Performance Checklist

- [ ] Connection pooling configured
- [ ] Critical indexes created
- [ ] Caching implemented for hot data
- [ ] Async/await used throughout
- [ ] Background tasks for heavy operations
- [ ] Pagination for large lists
- [ ] Prometheus metrics exposed
- [ ] Health checks with dependencies
- [ ] Load testing performed
- [ ] Bottlenecks identified and addressed