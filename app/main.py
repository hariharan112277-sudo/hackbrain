"""
Industrial Operating Brain (IOB) - Main Application Entry Point
Phase 5: Backend Integration, Performance & Security Optimization
Stage 6: REST API Routing & Response Matrix Complete
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.core.config import settings
from app.core.dependencies import (
    bootstrap_repository_subsystem,
    shutdown_repository_subsystem,
)
from app.core.logging_config import setup_logging
from app.core.security import SecurityHeadersMiddleware
from app.core.exceptions import (
    IOBException,
    ResourceNotFoundError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
)
<<<<<<< HEAD
from app.api import auth, users, industrial, dashboard, ws

=======
from app.api import auth, users, industrial, dashboard
from app.api.v1.users import router as stage6_user_router
>>>>>>> 758921e (trackA-6)

# Setup structured logging
setup_logging()
logger = structlog.get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    logger.info("io_application_starting", version=settings.APP_VERSION)
    
    # Startup: Initialize connections, warm caches, etc.
    # Start MQTT bridge and WebSocket queue distributor
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
        
        await stop_distributor()
        await mqtt_bridge_instance.stop()
        logger.info("io_mqtt_and_distributor_stopped")
    except Exception as e:
        logger.error("io_shutdown_services_failed", error=str(e))



def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Core System API",
        description="Production Architecture Stack - Stage 6 Rest Layer Complete",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # Browser and CORS security boundaries.
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global custom architectural Exception Middleware catch handler
    @app.exception_handler(RuntimeError)
    async def production_runtime_exception_handler(request: Request, exc: RuntimeError):
        """
        Prevents runtime system leaks or stack trace dumps from bubbling up to external consumers,
        structuring a safe default JSON payload error response template.
        """
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": "SYSTEM_RUNTIME_GATED_ERROR",
                "message": "A critical workspace execution restriction forced an operation cancellation.",
                "details": str(exc) if settings.ENV != "production" else "Internal processing boundary error."
            }
        )

    # Global Exception Handlers (existing Phase 5)
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
            content={"error": exc.error_code, "message": exc.detail, "details": exc.details},
        )

    @app.exception_handler(ResourceNotFoundError)
    async def not_found_handler(request: Request, exc: ResourceNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"error": "NOT_FOUND", "message": str(exc)},
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=422,
            content={"error": "VALIDATION_ERROR", "message": str(exc), "details": exc.details},
        )

    @app.exception_handler(AuthenticationError)
    async def auth_error_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(
            status_code=401,
            content={"error": "UNAUTHORIZED", "message": str(exc)},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(AuthorizationError)
    async def forbidden_handler(request: Request, exc: AuthorizationError):
        return JSONResponse(
            status_code=403,
            content={"error": "FORBIDDEN", "message": str(exc)},
        )

    # Health Check Endpoint
    @app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
    async def check_healthstatus():
        """Liveness check probe hook providing deployment verification insight."""
        return {"status": "healthy", "environment": settings.ENV}

    @app.get("/ready", tags=["Health"])
    async def readiness_check():
        # Add actual readiness checks (DB, MQTT, etc.)
        return {"status": "ready", "service": settings.APP_NAME}

<<<<<<< HEAD
    # Include API Routers
    app.include_router(ws.router, tags=["WebSocket Telemetry"])
=======
    # Include Phase 5 API Routers
>>>>>>> 758921e (trackA-6)
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
    app.include_router(industrial.router, prefix="/api/v1/industrial", tags=["Industrial IoT"])
    app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])

    # Stage 6 — Versioned REST Matrix: User Subsystem Router
    # Standardize versioned module subrouting tables
    app.include_router(stage6_user_router, prefix="/api/v1")

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
