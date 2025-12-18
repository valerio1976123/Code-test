from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import auth, dashboard, devices, executions, schedules
from app.api.routes.market import router as market_router

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["schedules"])
api_router.include_router(executions.router, prefix="/executions", tags=["executions"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(market_router, prefix="", tags=["market"])
