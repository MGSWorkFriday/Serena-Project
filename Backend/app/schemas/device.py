# -*- coding: utf-8 -*-
"""Device MongoDB schema"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any

try:
    from bson import ObjectId
except ImportError:
    # Fallback for testing
    class ObjectId:
        def __init__(self, value=None):
            self.value = value
        def __str__(self):
            return str(self.value) if self.value else "test_id"


class Device:
    """Device document schema"""
    
    def __init__(
        self,
        device_id: str,
        name: Optional[str] = None,
        device_type: str = "polar_h10",
        created_at: Optional[datetime] = None,
        last_seen: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        _id: Optional[ObjectId] = None,
    ):
        self._id = _id or ObjectId()
        self.device_id = device_id
        self.name = name
        self.type = device_type
        self.created_at = created_at or datetime.utcnow()
        self.last_seen = last_seen or datetime.utcnow()
        self.metadata = metadata or {}
    
    def to_dict(self) -> dict:
        """Convert to dictionary for MongoDB"""
        return {
            "_id": self._id,
            "device_id": self.device_id,
            "name": self.name,
            "type": self.type,
            "created_at": self.created_at,
            "last_seen": self.last_seen,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Device":
        """Create from dictionary"""
        return cls(
            _id=data.get("_id"),
            device_id=data["device_id"],
            name=data.get("name"),
            device_type=data.get("type", "polar_h10"),
            created_at=data.get("created_at"),
            last_seen=data.get("last_seen"),
            metadata=data.get("metadata", {}),
        )
    
    def update_last_seen(self):
        """Update last_seen timestamp"""
        self.last_seen = datetime.utcnow()
