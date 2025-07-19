"""
Main FastAPI application for InventorySync Shopify App
"""
import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="InventorySync Shopify App",
    description="Inventory synchronization and management for Shopify stores",
    version="1.0.0",
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src * 'unsafe-inline' 'unsafe-eval'; frame-ancestors 'self' https://*.myshopify.com https://admin.shopify.com https://*.shopify.com;"
    response.headers["Access-Control-Allow-Origin"] = "*"
    if "X-Frame-Options" in response.headers:
        del response.headers["X-Frame-Options"]
    return response


# Configure headers for Shopify embedding
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

class ShopifyHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = "default-src * 'unsafe-inline' 'unsafe-eval'; frame-ancestors * https://*.myshopify.com https://admin.shopify.com https://*.shopify.com;"
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers.remove("X-Frame-Options")
        return response

# Add security headers middleware first
app.add_middleware(ShopifyHeadersMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import security middleware
try:
    from middleware.webhook_verification import WebhookVerificationMiddleware
    from middleware.rate_limiting import RateLimitMiddleware
    from middleware.security_headers_fixed import SecurityHeadersMiddleware
    
    # Add security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Add rate limiting (60 requests per minute per shop)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
    
    # Add webhook verification if secret is available
    webhook_secret = os.environ.get("SHOPIFY_WEBHOOK_SECRET")
    if webhook_secret:
        app.add_middleware(WebhookVerificationMiddleware, webhook_secret=webhook_secret)
        logger.info("Webhook verification middleware enabled")
    else:
        logger.warning("SHOPIFY_WEBHOOK_SECRET not set, webhook verification disabled")
        
    logger.info("Security middleware configured")
except ImportError as e:
    logger.warning(f"Security middleware not available: {e}")

# Import and register routers with try-except blocks
def register_routers():
    """Register all available API routers"""
    
    # Health endpoints
    try:
        from api.health import router as health_router
        app.include_router(health_router, tags=["health"])
        logger.info("Health router registered")
    except ImportError as e:
        logger.warning(f"Health router not available: {e}")

    # Authentication - Use full OAuth-enabled router
    try:
        from api.auth import router as auth_router
        app.include_router(auth_router, tags=["authentication"])
        logger.info("Full OAuth auth router registered")
    except ImportError:
        try:
            from api.auth_simple import router as auth_router
            app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
            logger.info("Simple auth router registered (fallback)")
        except ImportError as e:
            logger.warning(f"No auth router available: {e}")

    # Inventory Management - Use simplified version
    try:
        from api.inventory_simple import router as inventory_router
        app.include_router(inventory_router, prefix="/api/inventory", tags=["inventory"])
        logger.info("Inventory router registered")
    except ImportError as e:
        logger.warning(f"Inventory router not available: {e}")

    # Locations
    try:
        from api.locations_simple import router as locations_router
        app.include_router(locations_router, prefix="/api/locations", tags=["locations"])
        logger.info("Locations router registered")
    except ImportError as e:
        logger.warning(f"Locations router not available: {e}")

    # Alerts
    try:
        from api.alerts_simple import router as alerts_router
        app.include_router(alerts_router, prefix="/api/alerts", tags=["alerts"])
        logger.info("Alerts router registered")
    except ImportError as e:
        logger.warning(f"Alerts router not available: {e}")

    # Webhooks
    try:
        from api.webhooks_simple import router as webhooks_router
        app.include_router(webhooks_router, prefix="/api/webhooks", tags=["webhooks"])
        logger.info("Webhooks router registered")
    except ImportError as e:
        logger.warning(f"Webhooks router not available: {e}")

    # Reports
    try:
        from api.reports_simple import router as reports_router
        app.include_router(reports_router, prefix="/api/reports", tags=["reports"])
        logger.info("Reports router registered")
    except ImportError as e:
        logger.warning(f"Reports router not available: {e}")

    # Forecasting
    try:
        from api.forecasting_simple import router as forecasting_router
        app.include_router(forecasting_router, prefix="/api/forecasting", tags=["forecasting"])
        logger.info("Forecasting router registered")
    except ImportError as e:
        logger.warning(f"Forecasting router not available: {e}")

    # Workflows
    try:
        from api.workflows_simple import router as workflows_router
        app.include_router(workflows_router, prefix="/api/workflows", tags=["workflows"])
        logger.info("Workflows router registered")
    except ImportError as e:
        logger.warning(f"Workflows router not available: {e}")

    # GDPR - Register under /api/webhooks for GDPR compliance endpoints
    try:
        from api.gdpr import router as gdpr_router
        app.include_router(gdpr_router, tags=["gdpr"])
        logger.info("GDPR router registered")
    except ImportError as e:
        logger.warning(f"GDPR router not available: {e}")

    # Monitoring
    try:
        from api.monitoring import router as monitoring_router
        app.include_router(monitoring_router, prefix="/api/monitoring", tags=["monitoring"])
        logger.info("Monitoring router registered")
    except ImportError as e:
        logger.warning(f"Monitoring router not available: {e}")

    # Dashboard
    try:
        from api.dashboard import router as dashboard_router
        app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])
        logger.info("Dashboard router registered")
    except ImportError as e:
        logger.warning(f"Dashboard router not available: {e}")

    # Billing
    try:
        from api.billing import router as billing_router
        app.include_router(billing_router, prefix="/api/billing", tags=["billing"])
        logger.info("Billing router registered")
    except ImportError as e:
        logger.warning(f"Billing router not available: {e}")

    # Custom Fields - THE CORE FEATURE!
    try:
        from api.custom_fields_simple import router as custom_fields_router
        app.include_router(custom_fields_router, tags=["custom-fields"])
        logger.info("Custom fields router registered - Core feature enabled!")
    except ImportError:
        try:
            from api.custom_fields import router as custom_fields_router
            app.include_router(custom_fields_router, tags=["custom-fields"])
            logger.info("Custom fields router registered - Core feature enabled!")
        except ImportError as e:
            logger.error(f"CRITICAL: Custom fields router not available: {e}")

    # Templates for custom fields
    try:
        from api.templates_simple import router as templates_router
        app.include_router(templates_router, prefix="/api/templates", tags=["templates"])
        logger.info("Templates router registered")
    except ImportError as e:
        logger.warning(f"Templates router not available: {e}")
    
    # Metafields API - Direct Shopify integration!
    try:
        from api.metafields import router as metafields_router
        app.include_router(metafields_router, tags=["metafields"])
        logger.info("Metafields router registered - Direct Shopify integration enabled!")
    except ImportError as e:
        logger.warning(f"Metafields router not available: {e}")
    
    # Bulk Metafields API - High performance bulk operations!
    try:
        from api.metafields_bulk import router as bulk_metafields_router
        app.include_router(bulk_metafields_router, prefix="/api/v1/metafields", tags=["metafields-bulk"])
        logger.info("Bulk metafields router registered - High performance bulk operations enabled!")
    except ImportError:
        try:
            from app.api.v1.endpoints.metafields_bulk import router as bulk_metafields_router
            app.include_router(bulk_metafields_router, prefix="/api/v1/metafields", tags=["metafields-bulk"])
            logger.info("Bulk metafields router registered - High performance bulk operations enabled!")
        except ImportError as e:
            logger.warning(f"Bulk metafields router not available: {e}")

# Register all routers
register_routers()

# Root endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "InventorySync - Save $1,971/month on Custom Fields!",
        "version": "1.0.0",
        "status": "healthy",
        "value_proposition": {
            "monthly_savings": "$1,971",
            "annual_savings": "$23,652",
            "our_price": "$29-99/month",
            "shopify_plus_price": "$2,000+/month"
        },
        "quick_links": {
            "api_overview": "/api",
            "custom_fields_demo": "/api/custom-fields/value-proposition",
            "templates": "/api/custom-fields/templates",
            "interactive_docs": "/docs",
            "api_docs": "/redoc"
        },
        "core_feature": "Add unlimited custom fields to Shopify without upgrading to Plus!"
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
    """API root endpoint with available endpoints"""
    return {
        "message": "InventorySync API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "auth": "/api/auth",
            "inventory": "/api/inventory",
            "locations": "/api/locations",
            "alerts": "/api/alerts",
            "webhooks": "/api/webhooks",
            "reports": "/api/reports",
            "forecasting": "/api/forecasting",
            "workflows": "/api/workflows",
            "monitoring": "/api/monitoring",
            "dashboard": "/api/dashboard",
            "billing": "/api/billing",
            "custom_fields": "/api/custom-fields",
            "templates": "/api/templates"
        }
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
