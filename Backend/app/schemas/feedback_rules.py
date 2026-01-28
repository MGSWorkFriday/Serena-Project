# -*- coding: utf-8 -*-
"""Feedback Rules MongoDB schema"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    from bson import ObjectId
except ImportError:
    class ObjectId:
        def __init__(self, value=None):
            self.value = value
        def __str__(self):
            return str(self.value) if self.value else "test_id"


class FeedbackMessage:
    """Feedback message structure"""
    
    def __init__(
        self,
        weight: int,
        text: str,
        audio_text: str,
    ):
        self.weight = weight
        self.text = text
        self.audio_text = audio_text
    
    def to_dict(self) -> dict:
        return {
            "weight": self.weight,
            "text": self.text,
            "audio_text": self.audio_text,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "FeedbackMessage":
        return cls(
            weight=data["weight"],
            text=data["text"],
            audio_text=data["audio_text"],
        )


class FeedbackCategory:
    """Feedback category structure"""
    
    def __init__(
        self,
        messages: List[FeedbackMessage],
        threshold_sec: Optional[float] = None,
        threshold_pct: Optional[float] = None,
    ):
        self.messages = messages
        self.threshold_sec = threshold_sec
        self.threshold_pct = threshold_pct
    
    def to_dict(self) -> dict:
        result = {
            "messages": [msg.to_dict() for msg in self.messages],
        }
        if self.threshold_sec is not None:
            result["threshold_sec"] = self.threshold_sec
        if self.threshold_pct is not None:
            result["threshold_pct"] = self.threshold_pct
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> "FeedbackCategory":
        return cls(
            messages=[FeedbackMessage.from_dict(msg) for msg in data.get("messages", [])],
            threshold_sec=data.get("threshold_sec"),
            threshold_pct=data.get("threshold_pct"),
        )


class FeedbackRules:
    """Feedback Rules document schema (Single Document Pattern)"""
    
    DOCUMENT_ID = "feedback_rules_singleton"
    
    @classmethod
    def get_document_id(cls):
        """Get the document ID as ObjectId or string"""
        try:
            from bson import ObjectId
            # Use a fixed ObjectId for the singleton document
            # This is a deterministic ObjectId based on the string
            try:
                # Create ObjectId from hex string (24 chars)
                # Use a consistent hex string: "feedback_rules_singleton" -> hex
                hex_str = "feed" + "back" + "rules" + "singleton"[:12]  # 24 chars
                # Pad to 24 chars if needed
                while len(hex_str) < 24:
                    hex_str += "0"
                hex_str = hex_str[:24]
                return ObjectId(hex_str)
            except:
                # Fallback: use a simple query by a unique field instead
                return None
        except ImportError:
            # Fallback if bson not available
            return None
    
    def __init__(
        self,
        rules: Optional[Dict[str, Any]] = None,
        version: int = 1,
        updated_at: Optional[datetime] = None,
        _id: Optional[ObjectId] = None,
    ):
        self._id = _id or self.get_document_id()
        self.rules = rules or self._default_rules()
        self.version = version
        self.updated_at = updated_at or datetime.utcnow()
    
    def _default_rules(self) -> Dict[str, Any]:
        """Default feedback rules structure"""
        return {
            "blue": {
                "messages": [
                    {"weight": 10, "text": "We gaan de volgende ademhaling samen doen...", "audio_text": "We gaan de volgende ademhaling samen doen"}
                ],
                "threshold_sec": 30.0
            },
            "green": {
                "messages": [
                    {"weight": 4, "text": "Perfect ritme!", "audio_text": "Perfect ritme"}
                ],
                "threshold_pct": 5.0
            },
            "orange": {
                "messages": [
                    {"weight": 5, "text": "Probeer het ritme weer op te pakken.", "audio_text": "Probeer het ritme weer op te pakken"}
                ],
                "threshold_pct": 15.0
            },
            "red_fast": {
                "messages": [
                    {"weight": 10, "text": "Je ademt niet correct.", "audio_text": "Je ademhaling is niet onder controlle. probeer dit weer op te pakken."}
                ]
            },
            "red_slow": {
                "messages": [
                    {"weight": 10, "text": "Je ademt niet correct.", "audio_text": "Je ademhaling is niet onder controlle. probeer dit weer op te pakken."}
                ]
            },
            "settings": {
                "stability_duration": 3.0,
                "repeat_interval": 7.0,
                "visual_interval": 7.0
            }
        }
    
    def to_dict(self) -> dict:
        """Convert to dictionary for MongoDB"""
        result = {
            "rules": self.rules,
            "version": self.version,
            "updated_at": self.updated_at,
        }
        if self._id:
            result["_id"] = self._id
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> "FeedbackRules":
        """Create from dictionary"""
        return cls(
            _id=data.get("_id"),
            rules=data.get("rules"),
            version=data.get("version", 1),
            updated_at=data.get("updated_at"),
        )
    
    def update_rules(self, new_rules: Dict[str, Any]):
        """Update rules and increment version"""
        self.rules = new_rules
        self.version += 1
        self.updated_at = datetime.utcnow()
    
    def get_settings(self) -> Dict[str, float]:
        """Get feedback settings"""
        return self.rules.get("settings", {})
    
    def get_category(self, category: str) -> Optional[Dict[str, Any]]:
        """Get category rules"""
        return self.rules.get(category)
