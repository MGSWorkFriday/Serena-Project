# -*- coding: utf-8 -*-
"""Feedback Pydantic models"""
from __future__ import annotations

from typing import Dict, Any
from pydantic import BaseModel


class FeedbackRulesResponse(BaseModel):
    """Response model for feedback rules"""
    rules: Dict[str, Any]
    version: int
    
    class Config:
        from_attributes = True


class FeedbackRulesUpdate(BaseModel):
    """Request model for updating feedback rules"""
    rules: Dict[str, Any]
