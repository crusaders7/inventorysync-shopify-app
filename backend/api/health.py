"""
Health check and system status endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import os
import psutil
import time
from datetime import datetime
from sqlalchemy import text
from database import get_db
from sqlalchemy.orm import Session
from utils.redis_client import get_redis_client
try:
    from app.core.logging import get_logger
except ImportError:
    # Fallback to basic logging
    import logging
    get_logger = logging.getLogger
from monitoring.prometheus_metrics import (
    active_stores, total_products_tracked,
    database_connections_active, sync_queue_size
)

router = APIRouter(prefix="/health", tags=["System Health"])
logger = get_logger('inventorysync.health')

@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "inventorysync-api",
        "version": "1.0.0"
    }

@router.get("/live")
async def liveness_probe():
    """Kubernetes liveness probe endpoint"""
    return {"status": "alive"}

@router.get("/ready")
async def readiness_probe(db: Session = Depends(get_db)):
    """Kubernetes readiness probe endpoint"""
    checks = {
        "database": False,
        "redis": False
    }
    
    # Check database connection
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    # Check Redis connection
    try:
        redis = get_redis_client()
        redis.ping()
        checks["redis"] = True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
    
    # Overall status
    all_healthy = all(checks.values())
    
    if not all_healthy:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not ready",
                "checks": checks
            }
        )
    
    return {
        "status": "ready",
        "checks": checks
    }

@router.get("/status")
async def system_status(db: Session = Depends(get_db)):
    """Detailed system status including metrics"""
    start_time = time.time()
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Database metrics
    db_status = "healthy"
    db_latency = 0
    try:
        db_start = time.time()
        db.execute(text("SELECT 1"))
        db_latency = (time.time() - db_start) * 1000  # ms
    except Exception as e:
        db_status = "unhealthy"
        logger.error(f"Database check failed: {e}")
    
    # Redis metrics
    redis_status = "healthy"
    redis_latency = 0
    redis_info = {}
    try:
        redis = get_redis_client()
        redis_start = time.time()
        redis.ping()
        redis_latency = (time.time() - redis_start) * 1000  # ms
        
        # Get Redis info
        info = redis.info()
        redis_info = {
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_mb": info.get("used_memory", 0) / 1024 / 1024,
            "total_commands_processed": info.get("total_commands_processed", 0)
        }
    except Exception as e:
        redis_status = "unhealthy"
        logger.error(f"Redis check failed: {e}")
    
    # Application metrics
    try:
        # Get store count from database
        store_count = db.execute(text("SELECT COUNT(*) FROM stores")).scalar()
        active_stores.set(store_count)
        
        # Get product count
        product_count = db.execute(text("SELECT COUNT(*) FROM products")).scalar()
        total_products_tracked.set(product_count)
        
        # Get sync queue size from Redis
        queue_size = 0
        try:
            redis = get_redis_client()
            queue_size = redis.llen("sync_queue")
            sync_queue_size.labels(queue_type="inventory").set(queue_size)
        except:
            pass
        
        application_metrics = {
            "active_stores": store_count,
            "total_products": product_count,
            "sync_queue_size": queue_size
        }
    except Exception as e:
        logger.error(f"Failed to get application metrics: {e}")
        application_metrics = {
            "error": "Failed to retrieve metrics"
        }
    
    # Build response
    status = {
        "status": "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": time.time() - start_time,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "system": {
            "cpu_percent": cpu_percent,
            "memory": {
                "percent": memory.percent,
                "available_gb": memory.available / 1024 / 1024 / 1024,
                "total_gb": memory.total / 1024 / 1024 / 1024
            },
            "disk": {
                "percent": disk.percent,
                "free_gb": disk.free / 1024 / 1024 / 1024,
                "total_gb": disk.total / 1024 / 1024 / 1024
            }
        },
        "services": {
            "database": {
                "status": db_status,
                "latency_ms": db_latency
            },
            "redis": {
                "status": redis_status,
                "latency_ms": redis_latency,
                **redis_info
            }
        },
        "application": application_metrics
    }
    
    return status

@router.get("/metrics/summary")
async def metrics_summary():
    """Get a summary of key metrics for dashboard display"""
    from utils.enhanced_logging import logger as enhanced_logger
    
    # Get performance metrics from enhanced logger
    perf_metrics = enhanced_logger.get_performance_metrics()
    
    # Additional business metrics would be fetched from database
    # This is a simplified version
    summary = {
        "timestamp": datetime.utcnow().isoformat(),
        "performance": perf_metrics,
        "alerts": {
            "active_count": 0,  # Would be fetched from database
            "last_24h_triggered": 0,
            "last_24h_resolved": 0
        },
        "sync_operations": {
            "last_24h_total": 0,  # Would be fetched from database
            "last_24h_successful": 0,
            "last_24h_failed": 0,
            "average_duration_seconds": 0
        }
    }
    
    return summary
