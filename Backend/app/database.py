# -*- coding: utf-8 -*-
"""MongoDB database connection"""
from __future__ import annotations

import logging
from typing import Optional

try:
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
    MOTOR_AVAILABLE = True
except ImportError:
    # Fallback for testing without motor
    MOTOR_AVAILABLE = False
    AsyncIOMotorClient = None
    AsyncIOMotorDatabase = None

from app.config import settings

logger = logging.getLogger(__name__)

# Global database client
client: Optional[AsyncIOMotorClient] = None
database: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongo():
    """Create database connection"""
    global client, database
    
    if not MOTOR_AVAILABLE:
        logger.warning("Motor not available - database features disabled")
        return
    
    try:
        client = AsyncIOMotorClient(
            settings.mongodb_uri,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000,
        )
        
        # Test connection
        await client.admin.command('ping')
        
        database = client[settings.mongo_database]
        
        logger.info(f"Connected to MongoDB: {settings.mongo_database}")
        
        # Create indexes on startup
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Close database connection"""
    global client, database
    
    if client:
        client.close()
        logger.info("Disconnected from MongoDB")
        client = None
        database = None


async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    if database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return database


async def create_indexes():
    """Create database indexes"""
    db = await get_database()
    
    logger.info("Creating database indexes...")
    
    # Device indexes
    await db.devices.create_index("device_id", unique=True)
    await db.devices.create_index("last_seen")
    
    # Session indexes
    await db.sessions.create_index([("device_id", 1), ("started_at", -1)])
    await db.sessions.create_index("session_id", unique=True)
    await db.sessions.create_index("status")
    
    # Signal Record indexes (time-series optimized)
    await db.signals.create_index([("device_id", 1), ("ts", -1)])
    await db.signals.create_index([("session_id", 1), ("signal", 1), ("ts", -1)])
    await db.signals.create_index([("signal", 1), ("ts", -1)])
    await db.signals.create_index("ts")  # For time-range queries
    
    # Technique indexes
    await db.techniques.create_index("name", unique=True)
    await db.techniques.create_index([("show_in_app", 1), ("is_active", 1)])
    
    # Parameter Set indexes
    await db.parameter_sets.create_index("version", unique=True)
    await db.parameter_sets.create_index("is_default")
    
    logger.info("Database indexes created successfully")
