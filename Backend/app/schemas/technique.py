# -*- coding: utf-8 -*-
"""Technique MongoDB schema"""
from __future__ import annotations

from datetime import datetime
from typing import List

try:
    from bson import ObjectId
except ImportError:
    class ObjectId:
        def __init__(self, value=None):
            self.value = value
        def __str__(self):
            return str(self.value) if self.value else "test_id"


class Technique:
    """Technique document schema"""
    
    def __init__(
        self,
        name: str,
        description: str,
        param_version: str,
        show_in_app: bool = False,
        protocol: Optional[List[List[int]]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        is_active: bool = True,
        _id: Optional[ObjectId] = None,
    ):
        self._id = _id or ObjectId()
        self.name = name
        self.description = description
        self.param_version = param_version
        self.show_in_app = show_in_app
        self.protocol = protocol or []
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.is_active = is_active
    
    def to_dict(self) -> dict:
        """Convert to dictionary for MongoDB"""
        return {
            "_id": self._id,
            "name": self.name,
            "description": self.description,
            "param_version": self.param_version,
            "show_in_app": self.show_in_app,
            "protocol": self.protocol,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_active": self.is_active,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Technique":
        """Create from dictionary"""
        return cls(
            _id=data.get("_id"),
            name=data["name"],
            description=data.get("description", ""),
            param_version=data.get("param_version", "Default"),
            show_in_app=data.get("show_in_app", False),
            protocol=data.get("protocol", []),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            is_active=data.get("is_active", True),
        )
    
    def update(self, **kwargs):
        """Update technique fields"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
