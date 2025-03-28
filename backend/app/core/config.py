"""
Configuration module for NigeriaJustice.AI

This module loads and provides configuration settings from environment
variables and configuration files.
"""

import os
import json
from typing import List, Dict, Optional, Union, Any
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file
    
    All settings are optional and have sensible defaults for development.
    In production, critical settings should be provided via environment variables.
    """
    
    # Application settings
    APP_NAME: str = "NigeriaJustice.AI"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "Nigerian Court AI System"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    RELOAD_ON_CHANGE: bool = ENVIRONMENT == "development"
    
    # Security settings
    API_KEY: str = os.getenv("API_KEY", "dev_api_key_for_testing_only")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev_secret_key_for_testing_only_change_in_production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    ALGORITHM: str = "HS256"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]  # Should be restricted in production
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    
    # Redis settings (for caching, message queue, etc.)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    USE_REDIS: bool = REDIS_URL is not None
    
    # Model paths
    TRANSCRIPTION_MODEL_PATH: str = os.getenv(
        "TRANSCRIPTION_MODEL_PATH", "models/transcription/whisper-nigerian"
    )
    SPEAKER_MODEL_PATH: str = os.getenv(
        "SPEAKER_MODEL_PATH", "models/speaker/nigerian-speaker-model"
    )
    NLP_MODEL_PATH: str = os.getenv(
        "NLP_MODEL_PATH", "models/nlp/nigerian-legal-model"
    )
    
    # API integration configuration
    IDENTITY_CONFIG_PATH: str = os.getenv(
        "IDENTITY_CONFIG_PATH", "config/identity_services.json"
    )
    
    # File storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "104857600"))  # 100 MB
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")
    
    # Feature flags
    ENABLE_VIRTUAL_COURT: bool = os.getenv("ENABLE_VIRTUAL_COURT", "True").lower() == "true"
    ENABLE_DECISION_SUPPORT: bool = os.getenv("ENABLE_DECISION_SUPPORT", "True").lower() == "true"
    ENABLE_WARRANT_TRANSFER: bool = os.getenv("ENABLE_WARRANT_TRANSFER", "True").lower() == "true"
    
    # Court configuration
    COURT_CONFIG_PATH: str = os.getenv(
        "COURT_CONFIG_PATH", "config/court_config.json"
    )
    COURT_CONFIG: Dict[str, Any] = {}
    
    def __init__(self, **data):
        super().__init__(**data)
        
        # Load court configuration
        self.load_court_config()
        
        # Create upload directory if it doesn't exist
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        
        # Create model directories if they don't exist
        model_dirs = [
            os.path.dirname(self.TRANSCRIPTION_MODEL_PATH),
            os.path.dirname(self.SPEAKER_MODEL_PATH),
            os.path.dirname(self.NLP_MODEL_PATH)
        ]
        
        for model_dir in model_dirs:
            if model_dir:
                os.makedirs(model_dir, exist_ok=True)
    
    def load_court_config(self):
        """Load court configuration from JSON file"""
        if os.path.exists(self.COURT_CONFIG_PATH):
            try:
                with open(self.COURT_CONFIG_PATH, "r") as f:
                    self.COURT_CONFIG = json.load(f)
            except Exception as e:
                print(f"Error loading court configuration: {e}")
        else:
            # Create a basic default configuration
            self.COURT_CONFIG = {
                "courts": [
                    {
                        "id": "fct-high-court",
                        "name": "FCT High Court",
                        "jurisdiction": "Federal Capital Territory",
                        "court_types": ["civil", "criminal", "family"],
                        "locations": [
                            {"id": "fct-1", "name": "FCT High Court 1", "address": "Maitama, Abuja"},
                            {"id": "fct-2", "name": "FCT High Court 2", "address": "Wuse, Abuja"}
                        ]
                    },
                    {
                        "id": "lagos-high-court",
                        "name": "Lagos State High Court",
                        "jurisdiction": "Lagos State",
                        "court_types": ["civil", "criminal", "family", "commercial"],
                        "locations": [
                            {"id": "lagos-1", "name": "Lagos High Court, Ikeja", "address": "Ikeja, Lagos"},
                            {"id": "lagos-2", "name": "Lagos High Court, Lagos Island", "address": "Lagos Island, Lagos"}
                        ]
                    }
                ],
