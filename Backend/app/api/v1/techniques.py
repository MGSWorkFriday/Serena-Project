# -*- coding: utf-8 -*-
"""Techniques management endpoints"""
from __future__ import annotations

import logging
from typing import List, Dict
from fastapi import APIRouter, HTTPException

from app.database import get_database
from app.models.technique import TechniqueCreate, TechniqueResponse
from app.schemas.technique import Technique

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=Dict[str, TechniqueResponse])
async def list_techniques():
    """Get all techniques (admin)"""
    db = await get_database()
    
    cursor = db.techniques.find({"is_active": True})
    techniques_docs = await cursor.to_list(length=None)
    
    result = {}
    for doc in techniques_docs:
        technique = Technique.from_dict(doc)
        result[technique.name] = TechniqueResponse(
            name=technique.name,
            description=technique.description,
            param_version=technique.param_version,
            show_in_app=technique.show_in_app,
            protocol=technique.protocol,
            _id=str(technique._id) if technique._id else None,
        )

    return result


@router.get("/public", response_model=Dict[str, TechniqueResponse])
async def list_public_techniques():
    """Get techniques marked as show_in_app=true and is_active=true"""
    db = await get_database()

    cursor = db.techniques.find({
        "show_in_app": True,
        "is_active": True
    })
    techniques_docs = await cursor.to_list(length=None)

    result = {}
    for doc in techniques_docs:
        technique = Technique.from_dict(doc)
        result[technique.name] = TechniqueResponse(
            name=technique.name,
            description=technique.description,
            param_version=technique.param_version,
            show_in_app=technique.show_in_app,
            protocol=technique.protocol,
            _id=str(technique._id) if technique._id else None,
        )

    logger.info("techniques/public: found %d docs, returning %d items", len(techniques_docs), len(result))
    return result


@router.get("/{name}", response_model=TechniqueResponse)
async def get_technique(name: str):
    """Get technique by name"""
    db = await get_database()
    
    technique_doc = await db.techniques.find_one({"name": name, "is_active": True})
    if not technique_doc:
        raise HTTPException(status_code=404, detail=f"Technique {name} not found")

    technique = Technique.from_dict(technique_doc)
    return TechniqueResponse(
        name=technique.name,
        description=technique.description,
        param_version=technique.param_version,
        show_in_app=technique.show_in_app,
        protocol=technique.protocol,
        _id=str(technique._id) if technique._id else None,
    )


@router.post("", response_model=TechniqueResponse, status_code=201)
async def create_technique(technique_data: TechniqueCreate):
    """Create or update a technique"""
    db = await get_database()
    
    technique = Technique(
        name=technique_data.name,
        description=technique_data.description,
        param_version=technique_data.param_version,
        show_in_app=technique_data.show_in_app,
        protocol=technique_data.protocol,
    )
    
    # Check if exists
    existing = await db.techniques.find_one({"name": technique.name})
    if existing:
        # Update existing
        technique._id = existing["_id"]
        technique.created_at = existing.get("created_at")
        technique.update(**technique_data.model_dump())
        
        await db.techniques.update_one(
            {"name": technique.name},
            {"$set": technique.to_dict()}
        )
    else:
        # Insert new
        result = await db.techniques.insert_one(technique.to_dict())
        technique._id = result.inserted_id

    return TechniqueResponse(
        name=technique.name,
        description=technique.description,
        param_version=technique.param_version,
        show_in_app=technique.show_in_app,
        protocol=technique.protocol,
        _id=str(technique._id) if technique._id else None,
    )


@router.delete("/{name}", status_code=204)
async def delete_technique(name: str):
    """Delete a technique (soft delete)"""
    db = await get_database()
    
    technique_doc = await db.techniques.find_one({"name": name})
    if not technique_doc:
        raise HTTPException(status_code=404, detail=f"Technique {name} not found")
    
    await db.techniques.update_one(
        {"name": name},
        {"$set": {"is_active": False}}
    )
    
    return None
