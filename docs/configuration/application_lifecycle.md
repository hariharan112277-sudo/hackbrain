# Core Lifespan Orchestration Matrix

## 1. Application Startup Sequence
1. **Bootstrapping Configs:** Load settings via Pydantic; immediately close boot phase if validation fails.
2. **Telemetry Init:** Bind global structured JSON loggers.
3. **Dependency Mapping:** Initialize global connection pooling for database layers and message systems using the FastAPI lifespan context manager.
4. **Exception Registration:** Hook global handler matrices into the ASGI instance.
5. **Middleware Attachment:** Layer CORS, Gzip compression, TrustedHost, and distributed request tracing middlewares.

## 2. Graceful Shutdown & Health Check Framework
- **Active Operations Check:** When a SIGTERM signals a shutdown, the application rejects incoming API traffic while processing active transactions.
- **Timeout Bounds:** Connection pools allow a 15-second grace window to safely drain running queries before breaking sockets.
- **Health Strategy:** Live endpoints (/healthz/liveness and /healthz/readiness) expose background verification checks on pools, ensuring zero packet drops during service handovers.