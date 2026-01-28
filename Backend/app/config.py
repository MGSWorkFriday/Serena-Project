# -*- coding: utf-8 -*-
"""Application configuration"""
from __future__ import annotations

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # MongoDB Configuration
    mongo_root_username: str = "admin"
    mongo_root_password: str = "changeme"
    mongo_database: str = "serena"
    mongo_host: str = "localhost"
    mongo_port: int = 27017
    mongo_uri: Optional[str] = None
    
    # Application
    app_env: str = "development"
    app_debug: bool = True
    log_level: str = "INFO"
    
    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000,http://localhost:19006,http://localhost:8081,http://127.0.0.1:8081,http://127.0.0.1:3000,exp://localhost:8081"
    
    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    
    @property
    def mongodb_uri(self) -> str:
        """Build MongoDB connection URI"""
        if self.mongo_uri:
            return self.mongo_uri
        
        return (
            f"mongodb://{self.mongo_root_username}:{self.mongo_root_password}"
            f"@{self.mongo_host}:{self.mongo_port}/{self.mongo_database}"
            f"?authSource=admin"
        )
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list"""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env file


settings = Settings()
