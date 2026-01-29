# -*- coding: utf-8 -*-
"""Session Pydantic models"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """Request model for creating a session"""
    device_id: str = Field(..., description="Device identifier")
    technique_name: Optional[str] = Field(None, description="Breathing technique name")
    param_version: Optional[str] = Field(None, description="Parameter set version")
    metadata: Optional[dict] = Field(None, description="Additional session metadata (e.g. protocol)")


class SessionUpdate(BaseModel):
    """Request model for updating a session"""
    technique_name: Optional[str] = None
    param_version: Optional[str] = None
    target_rr: Optional[float] = None


class SessionResponse(BaseModel):
    """Response model for session"""
    session_id: str
    device_id: str
    started_at: datetime
    ended_at: Optional[datetime]
    technique_name: Optional[str]
    param_version: str
    target_rr: Optional[float]
    status: str
    duration_seconds: Optional[float] = None
    metadata: Optional[dict] = None
    
    class Config:
        from_attributes = True
