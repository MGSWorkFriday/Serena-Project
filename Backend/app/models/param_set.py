# -*- coding: utf-8 -*-
"""Parameter Set Pydantic models"""
from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field


class ParameterSetResponse(BaseModel):
    """Response model for parameter set"""
    version: str
    BP_LOW_HZ: float
    BP_HIGH_HZ: float
    MWA_QRS_SEC: float
    MWA_BEAT_SEC: float
    MIN_SEG_SEC: float
    MIN_RR_SEC: float
    QRS_HALF_SEC: float
    HEARTBEAT_WINDOW: int
    FFT_LENGTH: int
    FREQ_RANGE_CB: List[float]
    SMOOTH_WIN: int
    BPM_MIN: float
    BPM_MAX: float
    HARMONIC_RATIO: float
    BUFFER_SIZE: int
    is_default: bool
    
    class Config:
        from_attributes = True


class ParameterSetCreate(BaseModel):
    """Request model for creating a parameter set"""
    version: str = Field(..., description="Version identifier")
    BP_LOW_HZ: float
    BP_HIGH_HZ: float
    MWA_QRS_SEC: float
    MWA_BEAT_SEC: float
    MIN_SEG_SEC: float
    MIN_RR_SEC: float
    QRS_HALF_SEC: float
    HEARTBEAT_WINDOW: int
    FFT_LENGTH: int
    FREQ_RANGE_CB: List[float] = Field(..., description="Frequency range [low, high]")
    SMOOTH_WIN: int
    BPM_MIN: float
    BPM_MAX: float
    HARMONIC_RATIO: float
    BUFFER_SIZE: int
    is_default: bool = False
