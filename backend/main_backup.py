"""
Main FastAPI application for InventorySync Shopify App
"""
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    from api.inventory import router as inventory_router
    # Don't add prefix here since router already defines it
    app.include_router(inventory_router, tags=["inventory"])
except ImportError:
    logger.warning("Inventory router not available")

try:
    from api.locations import router as locations_router
    app.include_router(locations_router, prefix="/api/locations", tags=["locations"])
except ImportError:
    logger.warning("Locations router not available")

try:
    from api.alerts import router as alerts_router
    app.include_router(alerts_router, prefix="/api/alerts", tags=["alerts"])
except ImportError:
    logger.warning("Alerts router not available")

try:
    from api.webhooks import router as webhooks_router
    app.include_router(webhooks_router, prefix="/api/webhooks", tags=["webhooks"])
except ImportError:
    logger.warning("Webhooks router not available")

try:
    from api.reports import router as reports_router
    app.include_router(reports_router, prefix="/api/reports", tags=["reports"])
except ImportError:
    logger.warning("Reports router not available")

try:
    from api.forecasting import router as forecasting_router
    app.include_router(forecasting_router, prefix="/api/forecasting", tags=["forecasting"])
except ImportError:
    logger.warning("Forecasting router not available")

try:
    from api.workflows import router as workflows_router
    app.include_router(workflows_router, prefix="/api/workflows", tags=["workflows"])
except ImportError:
    logger.warning("Workflows router not available")

try:
    from api.gdpr import router as gdpr_router
    app.include_router(gdpr_router, prefix="/api/webhooks", tags=["gdpr"])
except ImportError:
    logger.warning("GDPR router not available")

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
