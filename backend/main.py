"""
Main FastAPI application for InventorySync Shopify App
"""
import os
try:
    from app.core.logging import get_logger, LoggingConfig
except ImportError:
    # Fallback to basic logging if our custom logging module isn't available
    import logging
    logging.basicConfig(level=logging.INFO)
    get_logger = logging.getLogger
    class LoggingConfig:
        @staticmethod
        def setup_logging():
            pass
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize logging
LoggingConfig.setup_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="InventorySync Shopify App",
    description="Inventory synchronization and management for Shopify stores",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include available routers
try:
    from api.health import router as health_router
    app.include_router(health_router, prefix="/health", tags=["health"])
except ImportError:
    logger.warning("Health router not available")

try:
    from api.auth import router as auth_router
    app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
except ImportError:
    logger.warning("Auth router not available")

try:
    from api.monitoring import router as monitoring_router
    app.include_router(monitoring_router, prefix="/api/monitoring", tags=["monitoring"])
except ImportError:
    logger.warning("Monitoring router not available")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "InventorySync Shopify App API",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "inventorysync-shopify-app",
        "version": "1.0.0"
    }

@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {
        "message": "InventorySync API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "api": "/api",
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
