"""
Integrated Application Entry Point.

Constructs the centralized FastAPI application with security middleware,
global exception handling, and Phase 4 business-service routers.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.security import SecurityHeadersMiddleware
from app.core.exceptions import (
    AppBaseException,
    custom_app_exception_handler,
    pydantic_validation_exception_handler,
)

# Router imports
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.industrial import router as industrial_router
from app.api.dashboard import router as dashboard_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Industrial Operating Brain API Framework",
        version="4.0.0",
        openapi_url="/api/v1/openapi.json",
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
    )

    # Core Security Middlewares
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception Handling
    app.add_exception_handler(AppBaseException, custom_app_exception_handler)
    app.add_exception_handler(
        RequestValidationError, pydantic_validation_exception_handler
    )

    # Mount Route Modules
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(industrial_router, prefix="/api/v1")
    app.include_router(dashboard_router, prefix="/api/v1")

    return app


app = create_app()
