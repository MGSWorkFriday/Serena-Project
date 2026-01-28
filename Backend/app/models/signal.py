# -*- coding: utf-8 -*-
"""Signal Pydantic models"""
from __future__ import annotations

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class RecordIngest(BaseModel):
    """Request model for ingesting a signal record"""
    signal: str = Field(..., description="Signal type: ecg, hr_derived, resp_rr, guidance, BreathTarget")
    ts: Optional[Union[int, float]] = Field(None, description="Timestamp in milliseconds")
    device_id: Optional[str] = Field(None, description="Device identifier")
    
    class Config:
        extra = "allow"  # Allow extra fields for signal-specific data


class SignalResponse(BaseModel):
    """Response model for signal record"""
    id: str = Field(..., alias="_id")
    device_id: str
    session_id: Optional[str]
    signal: str
    ts: int
    dt: str
    # Signal-specific fields (optional)
    samples: Optional[List[int]] = None
    bpm: Optional[float] = None
    estRR: Optional[float] = None
    tijd: Optional[str] = None
    inhale: Optional[str] = None
    exhale: Optional[str] = None
    text: Optional[str] = None
    audio_text: Optional[str] = None
    color: Optional[str] = None
    target: Optional[float] = None
    actual: Optional[float] = None
    TargetRR: Optional[float] = None
    breath_cycle: Optional[Dict[str, Union[int, float]]] = None
    technique: Optional[str] = None
    active_param_version: Optional[str] = None
    
    class Config:
        populate_by_name = True


class IngestResponse(BaseModel):
    """Response model for ingest endpoint"""
    accepted: int = Field(..., description="Number of records accepted")
    session_id: Optional[str] = Field(None, description="Active session ID if applicable")
