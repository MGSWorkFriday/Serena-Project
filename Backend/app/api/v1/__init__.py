# -*- coding: utf-8 -*-
"""API v1 routes"""
from __future__ import annotations

from fastapi import APIRouter
from datetime import datetime

from app.api.v1 import devices, sessions, signals, techniques, feedback, param_sets, ingest, stream

api_router = APIRouter(prefix="/api/v1", tags=["v1"])

# Include routers
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(signals.router, prefix="/signals", tags=["signals"])
api_router.include_router(techniques.router, prefix="/techniques", tags=["techniques"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
api_router.include_router(param_sets.router, prefix="/param_versions", tags=["parameter-sets"])
api_router.include_router(ingest.router, tags=["ingest"])
api_router.include_router(stream.router, tags=["stream"])


@api_router.get("/ping")
async def ping():
    """Lightweight connectivity check; no DB. Used for 'Offline' detection."""
    return {"pong": True}


@api_router.get("/status")
async def get_status():
    """Get detailed system status"""
    from app.database import database
    from app.config import settings

    db_status = "unknown"
    db_detail: str | None = None
    try:
        if database is not None:
            await database.client.admin.command("ping")
            db_status = "connected"
        else:
            db_status = "not_initialized"
    except Exception as e:
        db_status = "error"
        if getattr(settings, "app_debug", False):
            db_detail = str(e)

    out = {
        "status": "ok",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "0.4",
    }
    if db_detail is not None:
        out["database_error"] = db_detail
    return out
