#!/usr/bin/env python3
"""Demo seed script for hackathon presentation (Phase 6)."""
import asyncio
from app.core.database import get_session
from app.models.asset import Asset
from app.models.alert import Alert
from datetime import datetime

async def seed():
    async with get_session() as session:
        # Realistic industrial demo assets
        assets = [
            Asset(name="Pump-01", type="pump", tenant_id=1, status="healthy"),
            Asset(name="Conveyor-Belt-02", type="conveyor", tenant_id=1, status="healthy"),
            Asset(name="CNC-Mill-03", type="cnc", tenant_id=1, status="warning"),
        ]
        session.add_all(assets)
        await session.commit()
        print("Demo assets seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed())
