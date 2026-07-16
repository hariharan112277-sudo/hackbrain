"""
Industrial Operating Brain (IOB) - Phase 5 Backend Integration
Enterprise-grade FastAPI application for industrial IoT orchestration.
"""

__version__ = "5.0.0"
__author__ = "IOB Team - Member 1"
__description__ = "Phase 5: Backend Integration, Performance & Security Optimization"

from fastapi import APIRouter
from app.api import ai_proxy

# Create the main API router that the FastAPI application will include
router = APIRouter()

# Register your Stage 1 AI Gateway Proxy route
router.include_router(ai_proxy.router, prefix="/ai", tags=["ai"])