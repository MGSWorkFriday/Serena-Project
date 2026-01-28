# -*- coding: utf-8 -*-
"""Parameter sets endpoints"""
from __future__ import annotations

from typing import List
from fastapi import APIRouter, HTTPException

from app.database import get_database
from app.models.param_set import ParameterSetResponse, ParameterSetCreate
from app.schemas.parameter_set import ParameterSet

router = APIRouter()


@router.get("", response_model=List[str])
async def list_param_versions():
    """List all parameter set versions"""
    db = await get_database()
    
    cursor = db.parameter_sets.find({}, {"version": 1})
    versions = await cursor.to_list(length=None)
    
    return [v["version"] for v in versions]


@router.get("/{version}", response_model=ParameterSetResponse)
async def get_param_set(version: str):
    """Get parameter set by version"""
    db = await get_database()
    
    param_doc = await db.parameter_sets.find_one({"version": version})
    if not param_doc:
        raise HTTPException(status_code=404, detail=f"Parameter set {version} not found")
    
    param_set = ParameterSet.from_dict(param_doc)
    return ParameterSetResponse(**param_set.to_dict())


@router.post("", response_model=ParameterSetResponse, status_code=201)
async def create_param_set(param_data: ParameterSetCreate):
    """Create a new parameter set"""
    db = await get_database()
    
    # Check if version exists
    existing = await db.parameter_sets.find_one({"version": param_data.version})
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Parameter set {param_data.version} already exists"
        )
    
    param_set = ParameterSet(
        version=param_data.version,
        BP_LOW_HZ=param_data.BP_LOW_HZ,
        BP_HIGH_HZ=param_data.BP_HIGH_HZ,
        MWA_QRS_SEC=param_data.MWA_QRS_SEC,
        MWA_BEAT_SEC=param_data.MWA_BEAT_SEC,
        MIN_SEG_SEC=param_data.MIN_SEG_SEC,
        MIN_RR_SEC=param_data.MIN_RR_SEC,
        QRS_HALF_SEC=param_data.QRS_HALF_SEC,
        HEARTBEAT_WINDOW=param_data.HEARTBEAT_WINDOW,
        FFT_LENGTH=param_data.FFT_LENGTH,
        FREQ_RANGE_CB=param_data.FREQ_RANGE_CB,
        SMOOTH_WIN=param_data.SMOOTH_WIN,
        BPM_MIN=param_data.BPM_MIN,
        BPM_MAX=param_data.BPM_MAX,
        HARMONIC_RATIO=param_data.HARMONIC_RATIO,
        BUFFER_SIZE=param_data.BUFFER_SIZE,
        is_default=param_data.is_default,
    )
    
    result = await db.parameter_sets.insert_one(param_set.to_dict())
    param_set._id = result.inserted_id
    
    return ParameterSetResponse(**param_set.to_dict())


@router.patch("/{version}", response_model=ParameterSetResponse)
async def update_param_set(version: str, param_data: ParameterSetCreate):
    """Update a parameter set"""
    db = await get_database()
    
    param_doc = await db.parameter_sets.find_one({"version": version})
    if not param_doc:
        raise HTTPException(status_code=404, detail=f"Parameter set {version} not found")
    
    # Update fields
    update_data = param_data.model_dump(exclude={"version"}, exclude_unset=True)
    
    await db.parameter_sets.update_one(
        {"version": version},
        {"$set": update_data}
    )
    
    updated = await db.parameter_sets.find_one({"version": version})
    param_set = ParameterSet.from_dict(updated)
    
    return ParameterSetResponse(**param_set.to_dict())
