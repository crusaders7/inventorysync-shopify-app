"""
InventorySync Backend API
FastAPI-based backend for Shopify inventory management
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from datetime import datetime
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="InventorySync API",
    description="Smart inventory management for Shopify stores",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Will restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint - API status check"""
    return {
        "message": "InventorySync API is running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Health check for monitoring"""
    return {
        "status": "healthy",
        "service": "inventorysync-api",
        "timestamp": datetime.now().isoformat()
    }

# API v1 prefix
@app.get("/api/v1/status")
async def api_status():
    """API v1 status endpoint"""
    return {
        "api_version": "v1",
        "features": [
            "inventory_tracking",
            "smart_alerts", 
            "forecasting",
            "multi_location"
        ],
        "status": "development"
    }

if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )