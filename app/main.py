"""
Industrial Operating Brain (IOB) - Main Application Entry Point
Phase 3 & Phase 5: Backend Integration, Performance & Security Optimization,
Smoke Testing & Runtime Verification, Clean Boot

Phase 1 (Stability Hardening): serialization-safe global exception handlers are
registered below (RequestValidationError / Pydantic ValidationError /
SQLAlchemyError / global Exception) so malformed or hostile payloads can never
escalate a 4xx / DB error into a 500 Internal Server Error.

Phase 3 Verification Status: PASSED (see reports/phase3_smoke_testing_report.md)
- AI Gateway mapped (/api/v1/ai)
- MQTT bridge launches automatically (lifespan)
- WebSocket framework active (/api/v1/stream)
- Core business logic fully exposed
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import structlog

# Phase 1: required so the new global handlers can be registered by type.
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.dependencies import (
    bootstrap_repository_subsystem,
    shutdown_repository_subsystem,
)
from app.core.logging_config import setup_logging
from app.core.security import SecurityHeadersMiddleware
from app.core.middleware import CorrelationIdMiddleware
from app.core.tenant_isolation import TenantIsolationMiddleware
from app.core.payload_guard import PayloadSizeLimitMiddleware
from app.core.exceptions import (
    IOBException,
    ResourceNotFoundError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    # Phase 1 — serialization-safe canonical handlers
    request_validation_exception_handler,
    pydantic_validation_exception_handler,
    sqlalchemy_exception_handler,
    general_exception_handler,
)

# Combined all distinct module routers cleanly
from app.api import ai_proxy, auth, dashboard, users, ws
from app.api.v1.users import router as stage6_user_router
from app.core.health import router as health_router
from app.api.v1.assets import router as asset_router
from app.api.v1.alerts import router as alert_router

# Setup structured logging
setup_logging()
logger = structlog.get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Single ordered lifecycle: DB, edge transport, distributors, then traffic."""
    logger.info("io_startup_begin", version=settings.APP_VERSION)
    from app.core.database.engine import verify_database_connection
    from app.services.mqtt_bridge import mqtt_bridge_instance
    from app.api.ws import start_distributor, stop_distributor
    db_ok = await verify_database_connection(max_retries=3, retry_interval=1.0, timeout=5.0)
    if not db_ok and settings.is_production:
        raise RuntimeError("database liveness verification failed in production")
    logger.info("io_database_ready", healthy=db_ok)
    try:
        await mqtt_bridge_instance.start()
        start_distributor()
        logger.info("io_edge_and_websocket_ready", mqtt=mqtt_bridge_instance.connected)
    except Exception:
        logger.exception("io_transport_start_failed")
        if settings.is_production:
            raise
    logger.info("io_startup_complete")
    try:
        yield
    finally:
        logger.info("io_shutdown_begin")
        await stop_distributor()
        await mqtt_bridge_instance.stop()
        try:
            from shared.event_bus import redis_pool
            await redis_pool.aclose()
        except Exception:
            logger.warning("io_redis_close_skipped", exc_info=True)
        try:
            from app.core.database.engine import engine
            await engine.dispose()
        except Exception:
            logger.warning("io_database_pool_close_skipped", exc_info=True)
        logger.info("io_shutdown_complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Industrial Operating Brain - Enterprise IoT Orchestration Platform",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # Browser, CORS, and Tenant Security boundaries.
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(TenantIsolationMiddleware)
    # Phase 4 (R-4.5.1): 10MB payload restriction on the AI Gateway prefix.
    app.add_middleware(
        PayloadSizeLimitMiddleware,
        max_bytes=settings.AI_GATEWAY_MAX_PAYLOAD_BYTES,
        prefix="/api/v1/ai",
    )
    # Phase 4 (Section 9 — CORS & Cross-Origin Configuration):
    # Explicit method/header allow-lists instead of wildcards so that only
    # verified frontend origins and required auth headers are permitted.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Correlation-ID", "X-Requested-With"],
        expose_headers=["X-Correlation-ID"],
    )

    # Global & Standard Exception Handlers
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        if isinstance(exc.detail, dict):
            code = exc.detail.get("error_code") or exc.detail.get("error") or ("NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR")
            msg = exc.detail.get("message") or exc.detail.get("detail") or str(exc.detail)
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "success": False,
                    "error": {"code": code, "message": msg} if exc.status_code == 404 else code,
                    "error_code": code,
                    "message": msg,
                    "details": exc.detail.get("details"),
                },
            )
        # Phase 1: bodies that cannot be read/parsed (null bytes, truncated
        # streams, binary injection) surface as a 400 "There was an error
        # parsing the body". Remap to 422 so every malformed/hostile payload
        # yields a consistent VALIDATION_ERROR contract instead of a bare 400.
        if exc.status_code == 400 and isinstance(exc.detail, str) and "parsing the body" in exc.detail:
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "error": "VALIDATION_ERROR",
                    "message": "The request payload could not be parsed.",
                    "details": [exc.detail],
                },
            )
        if exc.status_code == 404:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "NOT_FOUND", "message": str(exc.detail)},
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": "HTTP_ERROR", "message": str(exc.detail)},
        )

    @app.exception_handler(IOBException)
    async def iob_exception_handler(request: Request, exc: IOBException):
        logger.error(
            "iob_exception",
            path=request.url.path,
            error_code=exc.error_code,
            detail=exc.detail,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": exc.error_code, "message": exc.detail, "details": exc.details},
        )

    @app.exception_handler(ResourceNotFoundError)
    async def not_found_handler(request: Request, exc: ResourceNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "NOT_FOUND", "message": str(exc)},
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=422,
            content={"success": False, "error": "VALIDATION_ERROR", "message": str(exc), "details": exc.details},
        )

    @app.exception_handler(AuthenticationError)
    async def auth_error_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(
            status_code=401,
            content={"success": False, "error": "UNAUTHORIZED", "message": str(exc)},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(AuthorizationError)
    async def forbidden_handler(request: Request, exc: AuthorizationError):
        return JSONResponse(
            status_code=403,
            content={"success": False, "error": "FORBIDDEN", "message": str(exc)},
        )

    # ── Phase 1 — Critical Backend Bug Fixes & Stability Hardening ────────────
    # Register the canonical, serialization-safe handlers. These guarantee that
    # un-decoded bytes / non-JSON types inside validation errors or DB failures
    # can never escalate a 4xx / DB error into a 500. The RequestValidationError
    # handler below REPLACES the previous inline handler that passed
    # exc.errors() straight to JSONResponse (which raised
    # "TypeError: Object of type bytes is not JSON serializable").
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(PydanticValidationError, pydantic_validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    # Global safety net — strict JSON contract for any unhandled exception.
    app.add_exception_handler(Exception, general_exception_handler)

    # Health Check Endpoint at Root
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
        }

    @app.get("/ready", tags=["Health"])
    async def readiness_check():
        return {"status": "ready", "service": settings.APP_NAME}

    # Include API Routers with full domain prefixes and monitoring
    app.include_router(health_router, prefix="/health", tags=["Monitoring"])
    app.include_router(health_router, prefix="/api/v1/health", tags=["Monitoring"])
    app.include_router(ws.router, prefix="/api/v1", tags=["WebSocket Telemetry"])
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
    app.include_router(stage6_user_router, prefix="/api/v1/stage6-users", tags=["Stage 6 Users"])
    app.include_router(asset_router, prefix="/api/v1/assets", tags=["Assets"])
    app.include_router(alert_router, prefix="/api/v1/alerts", tags=["Alerts"])
    app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
    app.include_router(ai_proxy.router, prefix="/api/v1/ai", tags=["AI Processing Gateway"])

    logger.info("io_application_created", routes=len(app.routes))
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_config=None,  # Use structlog instead
    )
