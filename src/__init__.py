"""IOB Data Engine - Stage 1 source package.

Industrial IoT data acquisition & simulation pipeline.
- simulator/    : Multi-threaded device simulator (publisher)
- ingestion/    : MQTT subscriber + Pydantic validator + Normalization Engine
- database/     : PostgreSQL repository (normalized telemetry)

Layered architecture: config_loader -> domain modules -> repository.
"""
__version__ = "1.0.0"
__owner__ = "Member 2"
