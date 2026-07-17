"""
Industrial Operating Brain (IOB) - Main Application Entry Point
Phase 5 & Phase 1: Backend Integration, Performance & Security Optimization, Clean Boot
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import structlog

from app.core.config import settings
from app.core.dependencies import (
    bootstrap_repository_subsystem,
    shutdown_repository_subsystem,
)
from app.core.logging_config import setup_logging
from app.core.security import SecurityHeadersMiddleware
from app.core.middleware import CorrelationIdMiddleware
from app.core.tenant_isolation import TenantIsolationMiddleware
from app.core.exceptions import (
    IOBException,
    ResourceNotFoundError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
)

# Combined all distinct module routers cleanly
from app.api import auth, users, industrial, dashboard, ws, ai_proxy
from app.api.v1.users import router as stage6_user_router
from app.core.health import router as health_router
from apps.core.api.asset import router as asset_router
from apps.core.api.alert import router as alert_router

# Setup structured logging
setup_logging()
logger = structlog.get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events with sequential check."""
    logger.info("io_application_starting", version=settings.APP_VERSION)
    
    # Stage 1: Verify async database connection pool (Section 4 & Section 6)
    try:
        from apps.core.database.engine import verify_database_connection
        db_ok = await verify_database_connection(max_retries=3, retry_interval=1.0, timeout=5.0)
        if db_ok:
            logger.info("io_database_pool_verified")
        else:
            logger.warning("io_database_pool_unverified_fallback")
    except Exception as exc:
        logger.warning("io_database_check_skipped", error=str(exc))

    # Stage 2: Verify Redis connection pool (Section 4 & Section 9)
    try:
        from shared.event_bus import redis_pool
        await asyncio.wait_for(redis_pool.ping(), timeout=5.0)
        logger.info("io_redis_cache_ready")
    except Exception as exc:
        logger.warning("io_redis_check_skipped_or_offline", error=str(exc))

    # Stage 3: Start MQTT bridge and WebSocket queue distributor (Section 8 & Section 9)
    try:
        from app.services.mqtt_bridge import mqtt_bridge_instance
        from app.api.ws import start_distributor
        
        await mqtt_bridge_instance.start()
        start_distributor()
        logger.info("io_mqtt_and_distributor_started")
    except Exception as e:
        logger.error("io_startup_services_failed", error=str(e))
        
    logger.info("io_startup_complete")
    
    yield
    
    # Shutdown: Clean up connections, flush logs, etc.
    logger.info("io_application_shutting_down")
    try:
        from app.services.mqtt_bridge import mqtt_bridge_instance
        from app.api.ws import stop_distributor
        from shared.event_bus import redis_pool
        
        await stop_distributor()
        await mqtt_bridge_instance.stop()
        await redis_pool.aclose()
        logger.info("io_mqtt_and_distributor_stopped")
    except Exception as e:
        logger.error("io_shutdown_services_failed", error=str(e))


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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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
        if exc.status_code == 404:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "NOT_FOUND", "message": str(exc.detail)},
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": "HTTP_ERROR", "message": str(exc.detail)},
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": "VALIDATION_ERROR",
                "message": "Invalid request parameters",
                "details": exc.errors(),
            },
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
