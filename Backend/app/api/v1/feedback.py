# -*- coding: utf-8 -*-
"""Feedback rules endpoints"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.database import get_database
from app.models.feedback import FeedbackRulesResponse, FeedbackRulesUpdate
from app.schemas.feedback_rules import FeedbackRules

router = APIRouter()


@router.get("/rules", response_model=FeedbackRulesResponse)
async def get_feedback_rules():
    """Get all feedback rules"""
    db = await get_database()
    
    # Use a query that will find the singleton document
    # Since we use a single document pattern, we can query for any document
    rules_doc = await db.feedback_rules.find_one({})
    
    if not rules_doc:
        # Create default rules
        feedback_rules = FeedbackRules()
        await db.feedback_rules.insert_one(feedback_rules.to_dict())
        return FeedbackRulesResponse(rules=feedback_rules.rules, version=feedback_rules.version)
    
    feedback_rules = FeedbackRules.from_dict(rules_doc)
    return FeedbackRulesResponse(rules=feedback_rules.rules, version=feedback_rules.version)


@router.post("/rules", response_model=FeedbackRulesResponse)
async def update_feedback_rules(rules_data: FeedbackRulesUpdate):
    """Update feedback rules"""
    db = await get_database()
    
    # Find the singleton document
    rules_doc = await db.feedback_rules.find_one({})
    
    if rules_doc:
        feedback_rules = FeedbackRules.from_dict(rules_doc)
        feedback_rules.update_rules(rules_data.rules)
        
        await db.feedback_rules.update_one(
            {"_id": rules_doc["_id"]},
            {"$set": feedback_rules.to_dict()}
        )
    else:
        feedback_rules = FeedbackRules(rules=rules_data.rules)
        await db.feedback_rules.insert_one(feedback_rules.to_dict())
    
    return FeedbackRulesResponse(rules=feedback_rules.rules, version=feedback_rules.version)


@router.get("/rules/settings", response_model=dict)
async def get_feedback_settings():
    """Get only feedback settings"""
    db = await get_database()
    
    rules_doc = await db.feedback_rules.find_one({})
    
    if not rules_doc:
        feedback_rules = FeedbackRules()
        return feedback_rules.get_settings()
    
    feedback_rules = FeedbackRules.from_dict(rules_doc)
    return feedback_rules.get_settings()
