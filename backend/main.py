"""
InventorySync Backend API
FastAPI-based backend for Shopify inventory management
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from middleware.security import setup_security_middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
import os
import time
from datetime import datetime
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import utilities
from utils.logging import logger, get_logger
from utils.exceptions import (
    InventorySyncException, 
    create_http_exception,
    internal_server_error
)
from config import settings
from utils.api_versioning import version_manager, get_api_configuration

# Import API routers
from api.auth import router as auth_router
from api.inventory import router as inventory_router
from api.alerts import router as alerts_router
from api.dashboard import router as dashboard_router
from api.custom_fields import router as custom_fields_router
from api.custom_fields_enhanced import router as custom_fields_enhanced_router
from api.workflows import router as workflows_router
from api.webhooks import router as webhooks_router
from api.reports import router as reports_router
from api.billing import router as billing_router
from api.integrations import router as integrations_router
from api.monitoring import router as monitoring_router
from api.forecasting import router as forecasting_router
from api.templates_simple import router as templates_router
from api.locations import router as locations_router
from api.multi_location import router as multi_location_router
from api.gdpr import router as gdpr_router

# Initialize FastAPI app
app = FastAPI(
    title="InventorySync API",
    description="""
    ## Enterprise-level inventory management for Shopify stores at startup-friendly prices.
    
    ### 🎯 Key Features
    - **Custom Fields**: Unlimited custom fields with JSONB storage and validation
    - **Workflow Automation**: Event-driven rules engine with complex condition evaluation  
    - **Advanced Reporting**: Build reports on any field with aggregations and filtering
    - **Smart Alerts**: Template-based alerts with analytics and auto-resolution
    - **Third-Party Integrations**: Complete REST API with webhooks and bulk operations
    
    ### 💡 Competitive Advantages
    - **90% cost savings** vs $2,500 enterprise tools
    - **Shopify native** embedded experience
    - **Instant setup** vs 6-month implementations
    - **API-first architecture** for unlimited customization
    
    ### 🚀 Plans & Pricing
    - **Starter ($49)**: Perfect for small businesses - 1K products, 5 custom fields
    - **Growth ($149)**: Growing businesses - 10K products, unlimited custom fields  
    - **Pro ($299)**: Enterprise features - unlimited everything, priority support
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "InventorySync API Support",
        "email": "api-support@inventorysync.com",
        "url": "https://inventorysync.com/support"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {
            "url": "https://api.inventorysync.com/api/v1",
            "description": "Production server"
        },
        {
            "url": "http://localhost:8000/api/v1", 
            "description": "Development server"
        }
    ]
)

# Set up the security middleware
environment = os.getenv('ENVIRONMENT', 'development').lower()
setup_security_middleware(app)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if hasattr(settings, 'cors_origins') else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rate limiting storage (in production, use Redis)
rate_limit_storage = {}

# Rate limiting middleware
@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    """Basic rate limiting middleware"""
    # Disable rate limiting in development
    if settings.debug or os.getenv("DISABLE_RATE_LIMIT", "").lower() == "true":
        return await call_next(request)
    
    client_ip = request.client.host if request.client else "unknown"
    
    # Skip rate limiting for health checks
    if request.url.path in ["/", "/health", "/api/v1/status"]:
        return await call_next(request)
    
    # Rate limiting: 600 requests per minute per IP (10 per second) - more reasonable for development
    current_time = time.time()
    window_start = current_time - 60  # 1 minute window
    
    # Clean old entries
    rate_limit_storage[client_ip] = [
        timestamp for timestamp in rate_limit_storage.get(client_ip, [])
        if timestamp > window_start
    ]
    
    # Check rate limit - increased to 600 for development
    if len(rate_limit_storage.get(client_ip, [])) >= 600:
        logger.warning(
            f"Rate limit exceeded for IP: {client_ip} - Path: {request.url.path}"
        )
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after": 60
            }
        )
    
    # Add current request timestamp
    if client_ip not in rate_limit_storage:
        rate_limit_storage[client_ip] = []
    rate_limit_storage[client_ip].append(current_time)
    
    return await call_next(request)


# Version headers middleware
@app.middleware("http")
async def add_version_headers(request: Request, call_next):
    """Add API version headers to all responses"""
    response = await call_next(request)
    
    # Add version headers if enabled
    if settings.api_version_header:
        version_headers = version_manager.get_cache_headers()
        for header, value in version_headers.items():
            response.headers[header] = value
    
    # Log API version usage
    if request.url.path.startswith("/api/"):
        # Extract version from path
        path_parts = request.url.path.split("/")
        if len(path_parts) > 2 and path_parts[2] in ["v1", "v2"]:
            version_manager.log_version_usage(
                version=path_parts[2],
                endpoint=request.url.path,
                method=request.method
            )
    
    return response

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = time.time()
    
    # Log request
    logger.debug(
        f"Incoming request: {request.method} {request.url.path}"
    )
    
    # Process request
    try:
        response = await call_next(request)
        
        # Calculate response time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"API: {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)"
        )
        
        # Add response time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path} - Response time: {process_time:.3f}s",
            exc_info=e
        )
        raise


# Exception handlers
@app.exception_handler(InventorySyncException)
async def inventorysync_exception_handler(request: Request, exc: InventorySyncException):
    """Handle custom InventorySync exceptions"""
    logger.error(
        f"InventorySync exception: {exc.message} - Path: {request.url.path} - Details: {exc.details}",
        exc_info=exc
    )
    
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.message,
            "details": exc.details,
            "type": "application_error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    logger.warning(
        f"Validation error on {request.url.path}: {str(exc)}"
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation failed",
            "details": exc.errors(),
            "type": "validation_error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(
        f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "type": "http_error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.critical(
        f"Unhandled exception on {request.url.path}: {str(exc)}",
        exc_info=exc
    )
    
    # Don't expose internal error details in production
    error_message = "Internal server error"
    if settings.debug:
        error_message = str(exc)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": error_message,
            "type": "internal_error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Security
security = HTTPBearer()

# Database startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        from database import init_db, check_database_health
        
        # Initialize database tables
        await init_db()
        logger.info("Database initialized successfully")
        
        # Check database health
        health_status = await check_database_health()
        if health_status:
            logger.info("Database health check passed")
        else:
            logger.warning("Database health check failed")
            
    except Exception as e:
        logger.error(f"Database startup failed: {e}")
        # Don't prevent app startup, but log the error

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up database connections on shutdown"""
    try:
        from database import close_db
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Database shutdown error: {e}")

# Include API routers
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(inventory_router)
app.include_router(alerts_router)
app.include_router(billing_router)
app.include_router(custom_fields_router)
app.include_router(custom_fields_enhanced_router)
app.include_router(workflows_router)
app.include_router(reports_router)
app.include_router(integrations_router)
app.include_router(monitoring_router)
app.include_router(webhooks_router)
app.include_router(forecasting_router)
app.include_router(templates_router)
app.include_router(locations_router)
app.include_router(multi_location_router)
app.include_router(gdpr_router)

# Mount static files for privacy policy, terms, etc.
app.mount("/static", StaticFiles(directory="static"), name="static")

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
    try:
        from database import check_database_health
        
        # Check database health
        db_healthy = await check_database_health()
        
        return {
            "status": "healthy" if db_healthy else "degraded",
            "service": "inventorysync-api",
            "database": "healthy" if db_healthy else "unhealthy",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "inventorysync-api",
            "database": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# API version info endpoint
@app.get("/api/version")
async def get_api_version_info():
    """Get current API version information"""
    return {
        "current_version": version_manager.current_version,
        "supported_versions": list(version_manager.VERSION_HISTORY.keys()),
        "version_details": version_manager.get_version_info(),
        "configuration": get_api_configuration()
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
        "status": "active",
        "cache_version": version_manager.cache_version,
        "deployment_id": version_manager.deployment_hash
    }

# API v2 prefix (if v2 is active)
@app.get("/api/v2/status")
async def api_v2_status():
    """API v2 status endpoint"""
    return {
        "api_version": "v2",
        "features": [
            "inventory_tracking",
            "smart_alerts", 
            "forecasting",
            "multi_location",
            "custom_fields",
            "workflows",
            "advanced_analytics"
        ],
        "status": "active" if version_manager.current_version == "v2" else "available",
        "cache_version": version_manager.cache_version,
        "deployment_id": version_manager.deployment_hash
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