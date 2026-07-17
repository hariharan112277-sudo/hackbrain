"""Shared Redis Event Bus — Phase 0 Remediation.
Non-blocking Pub/Sub interface for Track A → Track B notification dispatching.
Replaces direct cross-track import violations (e.g., alert_service → websocket_manager)."""
import json
import redis.asyncio as aioredis
from app.core.config import settings
import structlog

logger = structlog.get_logger("shared.event_bus")

# Initialize async Redis connection pool
redis_pool = aioredis.from_url(
    settings.REDIS_URL,
    max_connections=settings.REDIS_MAX_CONNECTIONS,
    socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
    decode_responses=True,
)


async def publish_alert(notification: dict) -> int:
    """Publish alert notification to pubsub:alerts."""
    payload = json.dumps(notification)
    result = await redis_pool.publish("pubsub:alerts", payload)
    logger.info("alert_published", channel="pubsub:alerts", subscribers=result)
    return result


async def publish_telemetry(event: dict) -> int:
    """Publish telemetry event to pubsub:telemetry."""
    payload = json.dumps(event)
    return await redis_pool.publish("pubsub:telemetry", payload)


async def subscribe_channel(channel: str):
    """Return async pubsub listener for Track B consumption."""
    pubsub = redis_pool.pubsub()
    await pubsub.subscribe(channel)
    return pubsub
