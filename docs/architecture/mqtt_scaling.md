# MQTT Broker Horizontal Scaling Guidelines

**Phase 0 Remediation — Architectural Gap Resolution**

Previously missing from repository documentation. Added per Phase 0 Engineering Baseline.

## Cluster Topology

- Deploy EMQX nodes behind a load balancer with sticky session support.
- Use a centralized Redis Pub/Sub integration (`redis://redis:6379/0`) as the event bus so WebSocket clients can receive messages regardless of which container node they connect to.
- Configure `shared_subscriptions` for MQTT clients to distribute load.

## Resource Limits

As enforced in `docker-compose.yml`:
- `cpus`: 0.5 per MQTT node
- `memory`: 128M reservation / 256M limit

## Backpressure Protocol

Under intense telemetry load:
1. Enable sliding-window memory buffers on the MQTT client.
2. Drop messages above the buffer limit rather than blocking the event loop.
3. Emit a metric (`telemetry_backpressure_dropped`) for monitoring.

## Connection Reuse

- Pool MQTT connections per container instance (max 5 concurrent clients per container).
- Reconnect loops must use `await asyncio.sleep(5)` to avoid CPU spin.
