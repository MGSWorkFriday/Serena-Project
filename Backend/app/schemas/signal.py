# -*- coding: utf-8 -*-
"""Signal Record MongoDB schema"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any, Union

try:
    from bson import ObjectId
except ImportError:
    class ObjectId:
        def __init__(self, value=None):
            self.value = value
        def __str__(self):
            return str(self.value) if self.value else "test_id"


class SignalRecord:
    """Signal Record document schema for time-series data"""
    
    SIGNAL_ECG = "ecg"
    SIGNAL_HR_DERIVED = "hr_derived"
    SIGNAL_RESP_RR = "resp_rr"
    SIGNAL_GUIDANCE = "guidance"
    SIGNAL_BREATH_TARGET = "BreathTarget"
    
    def __init__(
        self,
        device_id: str,
        signal: str,
        ts: int,  # Timestamp in milliseconds (epoch)
        dt: str,  # Human-readable datetime: "DD-MM-YYYY HH:MM:SS:MMM"
        session_id: Optional[str] = None,
        # ECG fields
        samples: Optional[List[int]] = None,
        # HR fields
        bpm: Optional[float] = None,
        # Resp RR fields
        estRR: Optional[float] = None,
        tijd: Optional[str] = None,
        inhale: Optional[str] = None,
        exhale: Optional[str] = None,
        # Guidance fields
        text: Optional[str] = None,
        audio_text: Optional[str] = None,
        color: Optional[str] = None,
        target: Optional[float] = None,
        actual: Optional[float] = None,
        # BreathTarget fields
        TargetRR: Optional[float] = None,
        breath_cycle: Optional[Dict[str, Union[int, float]]] = None,
        technique: Optional[str] = None,
        active_param_version: Optional[str] = None,
        # Metadata
        created_at: Optional[datetime] = None,
        _id: Optional[ObjectId] = None,
    ):
        self._id = _id or ObjectId()
        self.device_id = device_id
        self.session_id = session_id
        self.signal = signal
        self.ts = ts
        self.dt = dt
        self.created_at = created_at or datetime.utcnow()
        
        # Signal-specific fields
        self.samples = samples
        self.bpm = bpm
        self.estRR = estRR
        self.tijd = tijd
        self.inhale = inhale
        self.exhale = exhale
        self.text = text
        self.audio_text = audio_text
        self.color = color
        self.target = target
        self.actual = actual
        self.TargetRR = TargetRR
        self.breath_cycle = breath_cycle
        self.technique = technique
        self.active_param_version = active_param_version
    
    def to_dict(self) -> dict:
        """Convert to dictionary for MongoDB"""
        doc = {
            "_id": self._id,
            "device_id": self.device_id,
            "session_id": self.session_id,
            "signal": self.signal,
            "ts": self.ts,
            "dt": self.dt,
            "created_at": self.created_at,
        }
        
        # Add signal-specific fields (only if not None)
        if self.samples is not None:
            doc["samples"] = self.samples
        if self.bpm is not None:
            doc["bpm"] = self.bpm
        if self.estRR is not None:
            doc["estRR"] = self.estRR
        if self.tijd is not None:
            doc["tijd"] = self.tijd
        if self.inhale is not None:
            doc["inhale"] = self.inhale
        if self.exhale is not None:
            doc["exhale"] = self.exhale
        if self.text is not None:
            doc["text"] = self.text
        if self.audio_text is not None:
            doc["audio_text"] = self.audio_text
        if self.color is not None:
            doc["color"] = self.color
        if self.target is not None:
            doc["target"] = self.target
        if self.actual is not None:
            doc["actual"] = self.actual
        if self.TargetRR is not None:
            doc["TargetRR"] = self.TargetRR
        if self.breath_cycle is not None:
            doc["breath_cycle"] = self.breath_cycle
        if self.technique is not None:
            doc["technique"] = self.technique
        if self.active_param_version is not None:
            doc["active_param_version"] = self.active_param_version
        
        return doc
    
    @classmethod
    def from_dict(cls, data: dict) -> "SignalRecord":
        """Create from dictionary"""
        return cls(
            _id=data.get("_id"),
            device_id=data["device_id"],
            signal=data["signal"],
            ts=data["ts"],
            dt=data["dt"],
            session_id=data.get("session_id"),
            samples=data.get("samples"),
            bpm=data.get("bpm"),
            estRR=data.get("estRR"),
            tijd=data.get("tijd"),
            inhale=data.get("inhale"),
            exhale=data.get("exhale"),
            text=data.get("text"),
            audio_text=data.get("audio_text"),
            color=data.get("color"),
            target=data.get("target"),
            actual=data.get("actual"),
            TargetRR=data.get("TargetRR"),
            breath_cycle=data.get("breath_cycle"),
            technique=data.get("technique"),
            active_param_version=data.get("active_param_version"),
            created_at=data.get("created_at"),
        )
