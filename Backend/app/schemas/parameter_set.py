# -*- coding: utf-8 -*-
"""Parameter Set MongoDB schema"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

try:
    from bson import ObjectId
except ImportError:
    class ObjectId:
        def __init__(self, value=None):
            self.value = value
        def __str__(self):
            return str(self.value) if self.value else "test_id"


class ParameterSet:
    """Parameter Set document schema"""
    
    def __init__(
        self,
        version: str,
        BP_LOW_HZ: float,
        BP_HIGH_HZ: float,
        MWA_QRS_SEC: float,
        MWA_BEAT_SEC: float,
        MIN_SEG_SEC: float,
        MIN_RR_SEC: float,
        QRS_HALF_SEC: float,
        HEARTBEAT_WINDOW: int,
        FFT_LENGTH: int,
        FREQ_RANGE_CB: List[float],  # [low, high]
        SMOOTH_WIN: int,
        BPM_MIN: float,
        BPM_MAX: float,
        HARMONIC_RATIO: float,
        BUFFER_SIZE: int,
        is_default: bool = False,
        created_at: Optional[datetime] = None,
        _id: Optional[ObjectId] = None,
    ):
        self._id = _id or ObjectId()
        self.version = version
        self.BP_LOW_HZ = BP_LOW_HZ
        self.BP_HIGH_HZ = BP_HIGH_HZ
        self.MWA_QRS_SEC = MWA_QRS_SEC
        self.MWA_BEAT_SEC = MWA_BEAT_SEC
        self.MIN_SEG_SEC = MIN_SEG_SEC
        self.MIN_RR_SEC = MIN_RR_SEC
        self.QRS_HALF_SEC = QRS_HALF_SEC
        self.HEARTBEAT_WINDOW = HEARTBEAT_WINDOW
        self.FFT_LENGTH = FFT_LENGTH
        self.FREQ_RANGE_CB = FREQ_RANGE_CB
        self.SMOOTH_WIN = SMOOTH_WIN
        self.BPM_MIN = BPM_MIN
        self.BPM_MAX = BPM_MAX
        self.HARMONIC_RATIO = HARMONIC_RATIO
        self.BUFFER_SIZE = BUFFER_SIZE
        self.is_default = is_default
        self.created_at = created_at or datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for MongoDB"""
        return {
            "_id": self._id,
            "version": self.version,
            "BP_LOW_HZ": self.BP_LOW_HZ,
            "BP_HIGH_HZ": self.BP_HIGH_HZ,
            "MWA_QRS_SEC": self.MWA_QRS_SEC,
            "MWA_BEAT_SEC": self.MWA_BEAT_SEC,
            "MIN_SEG_SEC": self.MIN_SEG_SEC,
            "MIN_RR_SEC": self.MIN_RR_SEC,
            "QRS_HALF_SEC": self.QRS_HALF_SEC,
            "HEARTBEAT_WINDOW": self.HEARTBEAT_WINDOW,
            "FFT_LENGTH": self.FFT_LENGTH,
            "FREQ_RANGE_CB": self.FREQ_RANGE_CB,
            "SMOOTH_WIN": self.SMOOTH_WIN,
            "BPM_MIN": self.BPM_MIN,
            "BPM_MAX": self.BPM_MAX,
            "HARMONIC_RATIO": self.HARMONIC_RATIO,
            "BUFFER_SIZE": self.BUFFER_SIZE,
            "is_default": self.is_default,
            "created_at": self.created_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ParameterSet":
        """Create from dictionary"""
        return cls(
            _id=data.get("_id"),
            version=data["version"],
            BP_LOW_HZ=data["BP_LOW_HZ"],
            BP_HIGH_HZ=data["BP_HIGH_HZ"],
            MWA_QRS_SEC=data["MWA_QRS_SEC"],
            MWA_BEAT_SEC=data["MWA_BEAT_SEC"],
            MIN_SEG_SEC=data["MIN_SEG_SEC"],
            MIN_RR_SEC=data["MIN_RR_SEC"],
            QRS_HALF_SEC=data["QRS_HALF_SEC"],
            HEARTBEAT_WINDOW=data["HEARTBEAT_WINDOW"],
            FFT_LENGTH=data["FFT_LENGTH"],
            FREQ_RANGE_CB=data["FREQ_RANGE_CB"],
            SMOOTH_WIN=data["SMOOTH_WIN"],
            BPM_MIN=data["BPM_MIN"],
            BPM_MAX=data["BPM_MAX"],
            HARMONIC_RATIO=data["HARMONIC_RATIO"],
            BUFFER_SIZE=data["BUFFER_SIZE"],
            is_default=data.get("is_default", False),
            created_at=data.get("created_at"),
        )
    
    def to_params_dict(self) -> dict:
        """Convert to parameters dictionary (for algorithm use)"""
        return {
            "BP_LOW_HZ": self.BP_LOW_HZ,
            "BP_HIGH_HZ": self.BP_HIGH_HZ,
            "MWA_QRS_SEC": self.MWA_QRS_SEC,
            "MWA_BEAT_SEC": self.MWA_BEAT_SEC,
            "MIN_SEG_SEC": self.MIN_SEG_SEC,
            "MIN_RR_SEC": self.MIN_RR_SEC,
            "QRS_HALF_SEC": self.QRS_HALF_SEC,
            "HEARTBEAT_WINDOW": self.HEARTBEAT_WINDOW,
            "FFT_LENGTH": self.FFT_LENGTH,
            "FREQ_RANGE_CB": self.FREQ_RANGE_CB,
            "SMOOTH_WIN": self.SMOOTH_WIN,
            "BPM_MIN": self.BPM_MIN,
            "BPM_MAX": self.BPM_MAX,
            "HARMONIC_RATIO": self.HARMONIC_RATIO,
            "BUFFER_SIZE": self.BUFFER_SIZE,
        }
