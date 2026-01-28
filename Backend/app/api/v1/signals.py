# -*- coding: utf-8 -*-
"""Signal query endpoints"""
from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

try:
    from bson import ObjectId
except ImportError:
    ObjectId = None

from app.database import get_database
from app.models.signal import SignalResponse

router = APIRouter()


@router.get("", response_model=List[SignalResponse])
async def query_signals(
    device_id: Optional[str] = Query(None),
    session_id: Optional[str] = Query(None),
    signal: Optional[str] = Query(None),
    start_ts: Optional[int] = Query(None, description="Start timestamp (ms)"),
    end_ts: Optional[int] = Query(None, description="End timestamp (ms)"),
    limit: int = Query(1000, ge=1, le=10000),
    skip: int = Query(0, ge=0),
):
    """Query signals with filters"""
    db = await get_database()
    
    query = {}
    if device_id:
        query["device_id"] = device_id
    if session_id:
        query["session_id"] = session_id
    if signal:
        query["signal"] = signal
    if start_ts or end_ts:
        query["ts"] = {}
        if start_ts:
            query["ts"]["$gte"] = start_ts
        if end_ts:
            query["ts"]["$lte"] = end_ts
    
    cursor = db.signals.find(query).sort("ts", -1).skip(skip).limit(limit)
    signals = await cursor.to_list(length=limit)
    
    # Convert ObjectId to string
    for sig in signals:
        sig["_id"] = str(sig["_id"])
    
    return [SignalResponse(**sig) for sig in signals]


@router.get("/recent", response_model=dict)
async def get_recent_signals(
    signal: str = Query("hr_est", description="Signal type"),
    device_id: Optional[str] = Query(None),
    limit: int = Query(300, ge=1, le=1000),
):
    """Get recent signals (replaces old /recent endpoint)"""
    db = await get_database()
    
    query = {"signal": signal}
    if device_id:
        query["device_id"] = device_id
    
    cursor = db.signals.find(query).sort("ts", -1).limit(limit)
    signals = await cursor.to_list(length=limit)
    
    # Format response similar to old endpoint
    items = []
    for sig in reversed(signals):  # Oldest first
        if signal in ("hr_est", "hr_derived"):
            items.append({
                "ts": sig["ts"],
                "bpm": sig.get("bpm")
            })
        else:
            item = sig.copy()
            item["ts"] = sig["ts"]
            items.append(item)
    
    return {
        "signal": signal,
        "count": len(items),
        "items": items
    }


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(signal_id: str):
    """Get single signal record by ID"""
    db = await get_database()
    
    try:
        signal_doc = await db.signals.find_one({"_id": ObjectId(signal_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid signal ID format")
    
    if not signal_doc:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")
    
    signal_doc["_id"] = str(signal_doc["_id"])
    return SignalResponse(**signal_doc)
