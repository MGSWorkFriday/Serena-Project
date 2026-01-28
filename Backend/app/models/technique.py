# -*- coding: utf-8 -*-
"""Technique Pydantic models"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class TechniqueCreate(BaseModel):
    """Request model for creating/updating a technique"""
    name: str = Field(..., description="Technique name")
    description: str = Field(..., description="Technique description")
    param_version: str = Field(..., description="Parameter set version")
    show_in_app: bool = Field(False, description="Show in mobile app")
    protocol: List[List[int]] = Field(..., description="Breathing protocol: [[in, hold1, out, hold2, cycles], ...]")


class TechniqueResponse(BaseModel):
    """Response model for technique"""
    name: str
    description: str
    param_version: str
    show_in_app: bool
    protocol: List[List[int]]
    # Python mag geen _id (leading underscore); alias zorgt dat JSON "_id" blijft voor de frontend
    id: Optional[str] = Field(None, alias="_id", description="MongoDB ObjectId as string")

    class Config:
        from_attributes = True
        populate_by_name = True
