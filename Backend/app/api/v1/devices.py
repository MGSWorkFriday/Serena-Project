# -*- coding: utf-8 -*-
"""Device management endpoints"""
from __future__ import annotations

from typing import List
from fastapi import APIRouter, HTTPException, Query

try:
    from bson import ObjectId
except ImportError:
    # Fallback for testing without pymongo
    ObjectId = None

from app.database import get_database
from app.models.device import DeviceCreate, DeviceUpdate, DeviceResponse
from app.schemas.device import Device
from app.utils.exceptions import DeviceNotFoundError

router = APIRouter()


@router.get("", response_model=List[DeviceResponse])
async def list_devices(
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
):
    """List all devices"""
    db = await get_database()
    
    cursor = db.devices.find().sort("last_seen", -1).skip(skip).limit(limit)
    devices = await cursor.to_list(length=limit)
    
    return [DeviceResponse(**device) for device in devices]


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: str):
    """Get device by ID"""
    db = await get_database()
    
    device_doc = await db.devices.find_one({"device_id": device_id})
    if not device_doc:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    return DeviceResponse(**device_doc)


@router.post("", response_model=DeviceResponse, status_code=201)
async def create_device(device_data: DeviceCreate):
    """Register a new device"""
    db = await get_database()
    
    # Check if device already exists
    existing = await db.devices.find_one({"device_id": device_data.device_id})
    if existing:
        raise HTTPException(status_code=409, detail=f"Device {device_data.device_id} already exists")
    
    device = Device(
        device_id=device_data.device_id,
        name=device_data.name,
        device_type=device_data.device_type,
    )
    
    result = await db.devices.insert_one(device.to_dict())
    device._id = result.inserted_id
    
    return DeviceResponse(**device.to_dict())


@router.patch("/{device_id}", response_model=DeviceResponse)
async def update_device(device_id: str, device_data: DeviceUpdate):
    """Update device metadata"""
    db = await get_database()
    
    device_doc = await db.devices.find_one({"device_id": device_id})
    if not device_doc:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    update_data = device_data.model_dump(exclude_unset=True)
    if not update_data:
        return DeviceResponse(**device_doc)
    
    # Map device_type to type for database
    if "device_type" in update_data:
        update_data["type"] = update_data.pop("device_type")
    
    await db.devices.update_one(
        {"device_id": device_id},
        {"$set": update_data}
    )
    
    updated = await db.devices.find_one({"device_id": device_id})
    return DeviceResponse(**updated)


@router.get("/{device_id}/sessions", response_model=List[dict])
async def get_device_sessions(
    device_id: str,
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    status: str = Query(None),
):
    """Get sessions for a device"""
    db = await get_database()
    
    # Verify device exists
    device_doc = await db.devices.find_one({"device_id": device_id})
    if not device_doc:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    query = {"device_id": device_id}
    if status:
        query["status"] = status
    
    cursor = db.sessions.find(query).sort("started_at", -1).skip(skip).limit(limit)
    sessions = await cursor.to_list(length=limit)
    
    # Convert ObjectId to string
    for session in sessions:
        session["_id"] = str(session["_id"])
    
    return sessions
