"""
Enterprise Backend Application Factory.

Constructs the centralized FastAPI application with:
- Structured logging initialization
- Security headers middleware (XSS, clickjacking, HSTS, etc.)
- CORS middleware configuration
- Correlation ID and request logging middleware
- Global exception handler registration
- Lifecycle management (startup/shutdown hooks)
- Advanced liveness & readiness probes
- Core health-check and monitoring endpoints

Usage:
    from app.main import create_app
    app = create_app()

    # Or run directly:
    # uvicorn app.main:app --host 0.0.0.0 --port 8000
"""
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.exceptions import (
    AppBaseException,
    custom_app_exception_handler,
    iob_integration_exception_handler,
    pydantic_validation_exception_handler,
    global_starlette_exception_handler,
    default_unhandled_exception_handler,
)
from app.core.logging_config import (
    setup_structured_logging,
    CorrelationAndLoggingMiddleware,
)
from app.core.security import SecurityHeadersMiddleware
from app.core.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown procedures.
    Use this hook for connecting DB pools, warming caches, etc.
    """
    logger = logging.getLogger("app.lifecycle")
    logger.info(
        "Initializing Enterprise Backend Application...",
        extra={
            "extra_fields": {
                "service": settings.PROJECT_NAME,
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT,
                "debug": settings.DEBUG,
            }
        },
    )

    # Ready for DB connection setup in Phase 4
    yield

    logger.info(
        "Shutting down Enterprise Backend Application gracefully...",
        extra={
            "extra_fields": {
                "service": settings.PROJECT_NAME,
            }
        },
    )


def create_app() -> FastAPI:
    """Core factory constructing the enterprise FastAPI instances."""

    # 1. Initialize logging
    setup_structured_logging(
        log_level=settings.LOG_LEVEL,
        json_format=settings.JSON_LOGS,
    )

    # 2. Instantiate FastAPI
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        docs_url=f"{settings.API_PREFIX}/docs",
        redoc_url=f"{settings.API_PREFIX}/redoc",
        lifespan=lifespan,
    )

    # 3. Register Middleware Pipeline (Evaluated bottom-up / last added = first executed)
    # Order: SecurityHeaders → Correlation/Logging → CORS
    app.add_middleware(CORSMiddleware,
                       allow_origins=settings.ALLOWED_HOSTS,
                       allow_credentials=True,
                       allow_methods=["*"],
                       allow_headers=["*"])
    app.add_middleware(CorrelationAndLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    # 4. Global Exception Mappings
    # Register IOB integration exceptions first (more specific)
    from integration.exceptions import IOBIntegrationException
    app.add_exception_handler(IOBIntegrationException, iob_integration_exception_handler)
    app.add_exception_handler(AppBaseException, custom_app_exception_handler)
    app.add_exception_handler(
        RequestValidationError, pydantic_validation_exception_handler
    )
    app.add_exception_handler(
        StarletteHTTPException, global_starlette_exception_handler
    )
    app.add_exception_handler(Exception, default_unhandled_exception_handler)

    # 5. Include Health Probe Router with API prefix
    app.include_router(health_router, prefix=settings.API_PREFIX)

    # 6. Core Health-check route (legacy compatibility)
    @app.get("/health", tags=["Monitoring"])
    async def health_check():
        """System health and readiness validation endpoint."""
        return {
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
        }

    # 7. API Version Info
    @app.get(f"{settings.API_PREFIX}/info", tags=["Monitoring"])
    async def api_info():
        """Returns API metadata and feature flags."""
        return {
            "success": True,
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "features": {
                "structured_logging": settings.JSON_LOGS,
                "correlation_tracking": True,
                "realtime_streaming": settings.ENABLE_REALTIME_STREAMING,
                "opc_quality_checks": settings.ENFORCE_OPC_QUALITY_CHECKS,
                "security_headers": True,
                "jwt_auth": True,
            },
        }

    return app


# The primary application entrypoint (used by ASGI servers like Uvicorn)
app = create_app()
