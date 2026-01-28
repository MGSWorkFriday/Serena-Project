# -*- coding: utf-8 -*-
"""Session MongoDB schema"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any
import uuid

try:
    from bson import ObjectId
except ImportError:
    class ObjectId:
        def __init__(self, value=None):
            self.value = value
        def __str__(self):
            return str(self.value) if self.value else "test_id"


class Session:
    """Session document schema"""
    
    STATUS_ACTIVE = "active"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    
    def __init__(
        self,
        device_id: str,
        session_id: Optional[str] = None,
        started_at: Optional[datetime] = None,
        ended_at: Optional[datetime] = None,
        technique_name: Optional[str] = None,
        param_version: str = "v1_default",
        target_rr: Optional[float] = None,
        status: str = STATUS_ACTIVE,
        metadata: Optional[Dict[str, Any]] = None,
        _id: Optional[ObjectId] = None,
    ):
        self._id = _id or ObjectId()
        self.session_id = session_id or str(uuid.uuid4())
        self.device_id = device_id
        self.started_at = started_at or datetime.utcnow()
        self.ended_at = ended_at
        self.technique_name = technique_name
        self.param_version = param_version
        self.target_rr = target_rr
        self.status = status
        self.metadata = metadata or {}
    
    def to_dict(self) -> dict:
        """Convert to dictionary for MongoDB"""
        return {
            "_id": self._id,
            "session_id": self.session_id,
            "device_id": self.device_id,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "technique_name": self.technique_name,
            "param_version": self.param_version,
            "target_rr": self.target_rr,
            "status": self.status,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """Create from dictionary"""
        return cls(
            _id=data.get("_id"),
            session_id=data.get("session_id"),
            device_id=data["device_id"],
            started_at=data.get("started_at"),
            ended_at=data.get("ended_at"),
            technique_name=data.get("technique_name"),
            param_version=data.get("param_version", "v1_default"),
            target_rr=data.get("target_rr"),
            status=data.get("status", cls.STATUS_ACTIVE),
            metadata=data.get("metadata", {}),
        )
    
    def end(self, status: str = STATUS_COMPLETED):
        """End the session"""
        self.ended_at = datetime.utcnow()
        self.status = status
    
    def cancel(self):
        """Cancel the session"""
        self.end(self.STATUS_CANCELLED)
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate session duration in seconds"""
        if self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        return None
