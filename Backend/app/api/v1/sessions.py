# -*- coding: utf-8 -*-
"""Session management endpoints"""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query

try:
    from bson import ObjectId
except ImportError:
    ObjectId = None

from app.database import get_database
from app.models.session import SessionCreate, SessionUpdate, SessionResponse
from app.schemas.device import Device
from app.schemas.session import Session
from app.services.signal_processor import signal_processor
from app.utils.exceptions import SessionNotFoundError, DeviceNotFoundError

router = APIRouter()


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(session_data: SessionCreate):
    """Start a new session"""
    db = await get_database()

    # Ensure device exists: create if not found (e.g. app connected via BLE but never synced to backend)
    device_doc = await db.devices.find_one({"device_id": session_data.device_id})
    if not device_doc:
        device = Device(
            device_id=session_data.device_id,
            name=None,
            device_type="polar_h10",
        )
        await db.devices.insert_one(device.to_dict())
    
    # Check for active session
    active_session = await db.sessions.find_one({
        "device_id": session_data.device_id,
        "status": Session.STATUS_ACTIVE
    })
    
    if active_session:
        raise HTTPException(
            status_code=409,
            detail=f"Device {session_data.device_id} already has an active session"
        )
    
    session = Session(
        device_id=session_data.device_id,
        technique_name=session_data.technique_name,
        param_version=session_data.param_version or "v1_default",
    )
    
    result = await db.sessions.insert_one(session.to_dict())
    session._id = result.inserted_id
    
    response_dict = session.to_dict()
    response_dict["duration_seconds"] = session.duration_seconds
    
    return SessionResponse(**response_dict)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get session by ID"""
    db = await get_database()
    
    session_doc = await db.sessions.find_one({"session_id": session_id})
    if not session_doc:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    session = Session.from_dict(session_doc)
    response_dict = session.to_dict()
    response_dict["duration_seconds"] = session.duration_seconds
    
    return SessionResponse(**response_dict)


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(session_id: str, session_data: SessionUpdate):
    """Update session"""
    db = await get_database()
    
    session_doc = await db.sessions.find_one({"session_id": session_id})
    if not session_doc:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    update_data = session_data.model_dump(exclude_unset=True)
    if not update_data:
        session = Session.from_dict(session_doc)
        response_dict = session.to_dict()
        response_dict["duration_seconds"] = session.duration_seconds
        return SessionResponse(**response_dict)
    
    await db.sessions.update_one(
        {"session_id": session_id},
        {"$set": update_data}
    )
    
    updated = await db.sessions.find_one({"session_id": session_id})
    session = Session.from_dict(updated)
    response_dict = session.to_dict()
    response_dict["duration_seconds"] = session.duration_seconds
    
    return SessionResponse(**response_dict)


@router.post("/{session_id}/end", response_model=SessionResponse)
async def end_session(session_id: str):
    """End a session"""
    db = await get_database()
    
    session_doc = await db.sessions.find_one({"session_id": session_id})
    if not session_doc:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    session = Session.from_dict(session_doc)
    session.end()
    
    await db.sessions.update_one(
        {"session_id": session_id},
        {"$set": {"ended_at": session.ended_at, "status": session.status}}
    )
    
    # Clear signal processor buffers for this session
    signal_processor.clear_buffer(session_id)
    
    response_dict = session.to_dict()
    response_dict["duration_seconds"] = session.duration_seconds
    
    return SessionResponse(**response_dict)


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    device_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
):
    """List sessions with filters"""
    db = await get_database()
    
    query = {}
    if device_id:
        query["device_id"] = device_id
    if status:
        query["status"] = status
    if start_date or end_date:
        query["started_at"] = {}
        if start_date:
            query["started_at"]["$gte"] = start_date
        if end_date:
            query["started_at"]["$lte"] = end_date
    
    cursor = db.sessions.find(query).sort("started_at", -1).skip(skip).limit(limit)
    sessions_docs = await cursor.to_list(length=limit)
    
    sessions = []
    for doc in sessions_docs:
        session = Session.from_dict(doc)
        response_dict = session.to_dict()
        response_dict["duration_seconds"] = session.duration_seconds
        sessions.append(SessionResponse(**response_dict))
    
    return sessions
