"""
Main application entry point for NigeriaJustice.AI backend.

This module configures and starts the FastAPI application that serves
as the backend for the NigeriaJustice.AI system.
"""

import logging
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import os
from typing import Dict

# Import routers and services
from app.api.routes import (
    auth, 
    transcription, 
    case_management, 
    identity_verification,
    warrant_transfer,
    anonymization,
    virtual_court,
    judicial_support
)
from app.core.config import settings
from app.core.security import get_current_user, verify_api_key

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="NigeriaJustice.AI API",
    description="""
    API for the NigeriaJustice.AI system - A comprehensive AI-powered judicial system 
    designed specifically for the Nigerian court context.
    
    This system facilitates court proceedings transcription, case management, identity verification,
    and judicial decision support while ensuring data sovereignty and security.
    """,
    version="0.1.0",
    docs_url="/api/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/api/redoc" if os.getenv("ENVIRONMENT") != "production" else None,
)

# Add middleware for timing requests
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Add middleware for CORS - configure appropriately for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Should be restricted in production
    allow_headers=["*"],  # Should be restricted in production
)

# Exception handler for general exceptions
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred"},
    )

# Include routers with appropriate prefixes and tags
app.include_router(
    auth.router, 
    prefix="/api/auth", 
    tags=["Authentication"]
)
app.include_router(
    transcription.router, 
    prefix="/api/transcription", 
    tags=["Transcription"],
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    case_management.router, 
    prefix="/api/cases", 
    tags=["Case Management"],
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    identity_verification.router, 
    prefix="/api/identity", 
    tags=["Identity Verification"],
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    warrant_transfer.router, 
    prefix="/api/warrants", 
    tags=["Warrant Transfer"],
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    anonymization.router, 
    prefix="/api/anonymize", 
    tags=["Anonymization"],
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    virtual_court.router, 
    prefix="/api/virtual-court", 
    tags=["Virtual Court"],
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    judicial_support.router, 
    prefix="/api/judicial", 
    tags=["Judicial Support"],
    dependencies=[Depends(get_current_user)]
)

# Health check endpoint (no authentication required)
@app.get("/api/health", tags=["System"])
async def health_check():
    """Health check endpoint to verify system is running."""
    return {
        "status": "healthy",
        "version": app.version,
        "environment": os.getenv("ENVIRONMENT", "development")
    }

# System status endpoint (requires API key)
@app.get("/api/status", tags=["System"], dependencies=[Depends(verify_api_key)])
async def system_status():
    """System status endpoint with detailed information."""
    # In production, this would include actual system metrics
    return {
        "status": "operational",
        "version": app.version,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database_connection": "healthy",
        "services": {
            "transcription": "operational",
            "identity_verification": "operational",
            "case_management": "operational",
            "warrant_transfer": "operational",
            "judicial_support": "operational"
        },
        "uptime": "12 days, 5 hours, 23 minutes"
    }

# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """Root endpoint with basic API information."""
    return {
        "name": "NigeriaJustice.AI API",
        "version": app.version,
        "documentation": "/api/docs",
        "healthcheck": "/api/health"
    }

# Run the application
if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting NigeriaJustice.AI API server in {os.getenv('ENVIRONMENT', 'development')} mode")
    
    # Start the server
    uvicorn.run(
        "app.main:app", 
        host=settings.HOST, 
        port=settings.PORT,
        reload=settings.RELOAD_ON_CHANGE
    )
