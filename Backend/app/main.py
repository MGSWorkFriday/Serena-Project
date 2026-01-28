# -*- coding: utf-8 -*-
"""FastAPI application main"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.utils.logging import setup_logging
from app.api.v1 import api_router

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Serena Backend...")
    await connect_to_mongo()
    yield
    # Shutdown
    logger.info("Shutting down Serena Backend...")
    await close_mongo_connection()


# Create FastAPI app
app = FastAPI(
    title="Serena Backend API",
    version="0.4",
    description="Backend API for Serena breathing exercise application",
    lifespan=lifespan,
)

# CORS middleware
cors_list = settings.cors_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("CORS allowed origins: %s", cors_list)

# Include API routes
app.include_router(api_router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Serena Backend API",
        "version": "0.4",
        "docs": "/docs",
    }


# Health check endpoint
@app.get("/healthz")
async def healthz():
    """Health check endpoint"""
    from datetime import datetime
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
