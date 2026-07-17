# Redis Event Bus Specification — Phase 0 Remediation

**Purpose:** Decouple Track A (core persistence) from Track B (realtime AI) via non-blocking Redis Pub/Sub.

**Channels:**
- `pubsub:alerts` — Alert notifications published by Track A, consumed by Track B for WebSocket broadcast.
- `pubsub:telemetry` — Telemetry ingestion confirmation events.

**Implementation:**
```python
import redis.asyncio as redis
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

async def publish_alert(notification: dict):
    await redis_client.publish("pubsub:alerts", json.dumps(notification))
```

**Integration Point:**
- Track A: `app/services/industrial_service.py` should import `publish_alert` from `shared.event_bus` instead of importing `app.api.ws.manager` directly.
- Track B: `app/realtime_ai/streaming/workers.py` subscribes to `pubsub:alerts` asynchronously.
