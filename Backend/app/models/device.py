# -*- coding: utf-8 -*-
"""Device Pydantic models"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DeviceCreate(BaseModel):
    """Request model for creating a device"""
    device_id: str = Field(..., description="Unique device identifier")
    name: Optional[str] = Field(None, description="User-friendly device name")
    device_type: str = Field("polar_h10", description="Device type")


class DeviceUpdate(BaseModel):
    """Request model for updating a device"""
    name: Optional[str] = None
    device_type: Optional[str] = None


class DeviceResponse(BaseModel):
    """Response model for device"""
    device_id: str
    name: Optional[str]
    type: str
    created_at: datetime
    last_seen: datetime
    
    class Config:
        from_attributes = True
