# IOB Directory Structure

This document explains the Domain-Driven Design (DDD) separation between Track A (Core REST/DB) and Track B (Real-time / AI Streaming).

## Root
- `app/` - Main FastAPI application (Track A core + shared)
  - `api/v1/` - REST endpoints
  - `core/` - Shared infrastructure, security, middleware, logging
  - `models/` - SQLAlchemy models
  - `realtime_ai/` - Track B components
    - `gateway/` - AI proxy & protocol translator
    - `streaming/` - MQTT + WebSocket + Redis PubSub workers
- `apps/core/` - Legacy / alternative core package (DDD)
- `scripts/` - Demo seeding & utilities
- `tests/` - Comprehensive test suite
- `docs/` - Architecture & API documentation
- `deliverable/` - Phase reports & handover docs
- `infrastructure/` - Docker, config, simulators

Track A handles synchronous CRUD and auth.
Track B handles async real-time ingestion, broadcasting, and AI proxying.
