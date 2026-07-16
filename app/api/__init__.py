"""
Industrial Operating Brain (IOB) - Phase 5 Backend Integration
Enterprise-grade FastAPI application for industrial IoT orchestration.
"""

__version__ = "5.0.0"
__author__ = "IOB Team - Member 1"
__description__ = "Phase 5: Backend Integration, Performance & Security Optimization"

from fastapi import APIRouter
from app.api import ai_proxy, ws

router = APIRouter()

# Stage 1: Core AI Gateway API Route Registration
router.include_router(ai_proxy.router, prefix="/ai", tags=["ai"])

# Stage 2: Real-time Authenticated Telemetry Stream Channel
router.include_router(ws.router, tags=["websockets"])