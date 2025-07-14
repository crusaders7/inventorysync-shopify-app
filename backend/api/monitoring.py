"""
Monitoring API - System health and performance metrics
Internal monitoring endpoints for application observability
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List
from datetime import datetime, timedelta
# import psutil  # Not available in simplified setup

from utils.logging import logger

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class HealthCheck(BaseModel):
    status: str
    timestamp: str
    uptime_seconds: float
    database: str
    memory_usage_percent: float
    cpu_usage_percent: float


class PerformanceMetrics(BaseModel):
    uptime_seconds: float
    average_response_time_ms: float
    error_rate_percent: float
    memory_usage_percent: float
    cpu_usage_percent: float
    total_requests: int
    total_errors: int
    active_alerts: List[Dict[str, Any]]
    recent_alerts: List[Dict[str, Any]]


# =============================================================================
# HEALTH CHECK ENDPOINTS
# =============================================================================

@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        from database import check_database_health
        
        # Get system metrics
        memory_usage = 50.0  # Mock data for simplified setup
        cpu_usage = 25.0  # Mock data for simplified setup
        
        # Check database health
        try:
            db_healthy = await check_database_health()
            db_status = "healthy" if db_healthy else "unhealthy"
        except Exception as e:
            logger.error("Database health check failed", exc_info=e)
            db_status = "error"
        
        # Get uptime from logger performance monitor
        metrics = logger.get_performance_metrics()
        uptime = metrics.get('uptime_seconds', 0)
        
        # Determine overall status
        status = "healthy"
        if db_status != "healthy":
            status = "degraded"
        if memory_usage > 90 or cpu_usage > 90:
            status = "critical"
        
        return HealthCheck(
            status=status,
            timestamp=datetime.utcnow().isoformat(),
            uptime_seconds=uptime,
            database=db_status,
            memory_usage_percent=memory_usage,
            cpu_usage_percent=cpu_usage
        )
        
    except Exception as e:
        logger.error("Health check failed", exc_info=e)
        return HealthCheck(
            status="error",
            timestamp=datetime.utcnow().isoformat(),
            uptime_seconds=0,
            database="error",
            memory_usage_percent=0,
            cpu_usage_percent=0
        )


@router.get("/health/simple")
async def simple_health_check():
    """Simple health check for load balancers"""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# =============================================================================
# PERFORMANCE METRICS
# =============================================================================

@router.get("/metrics", response_model=PerformanceMetrics)
async def get_performance_metrics(
    admin_token: str = Header(..., alias="X-Admin-Token")
):
    """Get detailed performance metrics (admin only)"""
    
    # TODO: Validate admin token
    # For now, just check if header is present
    if not admin_token:
        raise HTTPException(status_code=401, detail="Admin token required")
    
    try:
        metrics = logger.get_performance_metrics()
        
        if metrics.get("monitoring") == "disabled":
            raise HTTPException(
                status_code=503, 
                detail="Monitoring is disabled. Set MONITORING_ENABLED=true to enable."
            )
        
        return PerformanceMetrics(**metrics)
        
    except Exception as e:
        logger.error("Failed to get performance metrics", exc_info=e)
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


@router.get("/metrics/summary")
async def get_metrics_summary():
    """Get basic metrics summary (no auth required)"""
    try:
        metrics = logger.get_performance_metrics()
        
        if metrics.get("monitoring") == "disabled":
            return {"monitoring": "disabled"}
        
        # Return only basic metrics without sensitive data
        return {
            "uptime_seconds": metrics.get("uptime_seconds", 0),
            "average_response_time_ms": metrics.get("average_response_time_ms", 0),
            "memory_usage_percent": metrics.get("memory_usage_percent", 0),
            "status": "healthy" if metrics.get("error_rate_percent", 0) < 5 else "degraded"
        }
        
    except Exception as e:
        logger.error("Failed to get metrics summary", exc_info=e)
        return {"status": "error", "message": "Failed to retrieve metrics"}


# =============================================================================
# ALERTS AND NOTIFICATIONS
# =============================================================================

@router.get("/alerts")
async def get_recent_alerts(
    limit: int = 10,
    admin_token: str = Header(..., alias="X-Admin-Token")
):
    """Get recent alerts (admin only)"""
    
    # TODO: Validate admin token
    if not admin_token:
        raise HTTPException(status_code=401, detail="Admin token required")
    
    try:
        alerts = logger.alert_manager.get_recent_alerts(limit)
        
        return {
            "alerts": alerts,
            "total_count": len(alerts),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get recent alerts", exc_info=e)
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


# =============================================================================
# SYSTEM INFORMATION
# =============================================================================

@router.get("/system")
async def get_system_info(
    admin_token: str = Header(..., alias="X-Admin-Token")
):
    """Get system information (admin only)"""
    
    # TODO: Validate admin token
    if not admin_token:
        raise HTTPException(status_code=401, detail="Admin token required")
    
    try:
        # Mock system information for simplified setup
        return {
            "system": {
                "cpu_count": 4,
                "cpu_percent": 25.0,
                "memory": {
                    "total_gb": 8.0,
                    "available_gb": 4.0,
                    "used_percent": 50.0
                },
                "disk": {
                    "total_gb": 100.0,
                    "free_gb": 50.0,
                    "used_percent": 50.0
                },
                "network": {
                    "bytes_sent": 1000000,
                    "bytes_recv": 2000000,
                    "packets_sent": 5000,
                    "packets_recv": 8000
                }
            },
            "process": {
                "pid": 1234,
                "memory_mb": 128.0,
                "cpu_percent": 5.0,
                "create_time": datetime.now().isoformat(),
                "num_threads": 10,
                "num_fds": 50
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get system info", exc_info=e)
        raise HTTPException(status_code=500, detail="Failed to retrieve system information")


# =============================================================================
# LOG ANALYSIS
# =============================================================================

@router.get("/logs/errors")
async def get_recent_errors(
    limit: int = 50,
    admin_token: str = Header(..., alias="X-Admin-Token")
):
    """Get recent error logs (admin only)"""
    
    # TODO: Validate admin token
    if not admin_token:
        raise HTTPException(status_code=401, detail="Admin token required")
    
    try:
        from pathlib import Path
        import json
        
        errors = []
        log_file = Path("logs/errors.log")
        
        if log_file.exists():
            with open(log_file, 'r') as f:
                lines = f.readlines()
                
            # Get last N lines
            recent_lines = lines[-limit:] if len(lines) > limit else lines
            
            for line in recent_lines:
                try:
                    # Try to parse as JSON first
                    if line.strip().startswith('{'):
                        error_data = json.loads(line.strip())
                        errors.append(error_data)
                    else:
                        # Plain text log
                        errors.append({
                            "timestamp": datetime.utcnow().isoformat(),
                            "message": line.strip(),
                            "level": "ERROR"
                        })
                except json.JSONDecodeError:
                    # Skip malformed lines
                    continue
        
        return {
            "errors": errors,
            "total_count": len(errors),
            "log_file": str(log_file),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get recent errors", exc_info=e)
        raise HTTPException(status_code=500, detail="Failed to retrieve error logs")


# =============================================================================
# CONFIGURATION
# =============================================================================

@router.get("/config")
async def get_monitoring_config(
    admin_token: str = Header(..., alias="X-Admin-Token")
):
    """Get monitoring configuration (admin only)"""
    
    # TODO: Validate admin token
    if not admin_token:
        raise HTTPException(status_code=401, detail="Admin token required")
    
    import os
    
    return {
        "monitoring_enabled": os.getenv('MONITORING_ENABLED', 'true').lower() == 'true',
        "log_level": os.getenv('LOG_LEVEL', 'INFO'),
        "environment": os.getenv('ENVIRONMENT', 'development'),
        "alert_thresholds": {
            "high_response_time_seconds": 5.0,
            "high_error_rate_percent": 5.0,
            "high_memory_usage_percent": 90.0,
            "high_cpu_usage_percent": 90.0
        },
        "retention": {
            "metrics_entries": 100,
            "alerts_entries": 50,
            "logs_days": 30
        }
    }


# =============================================================================
# TESTING ENDPOINTS (Development only)
# =============================================================================

@router.post("/test/error")
async def trigger_test_error(
    admin_token: str = Header(..., alias="X-Admin-Token")
):
    """Trigger a test error for monitoring validation (admin only)"""
    
    # TODO: Validate admin token and environment
    if not admin_token:
        raise HTTPException(status_code=401, detail="Admin token required")
    
    import os
    if os.getenv('ENVIRONMENT', 'development') == 'production':
        raise HTTPException(status_code=403, detail="Test endpoints disabled in production")
    
    # Trigger a test error
    logger.error("Test error triggered via monitoring API", test_error=True)
    
    # Also trigger performance recording
    logger.performance_monitor.record_error("test_error")
    
    return {
        "message": "Test error triggered successfully",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/test/alert")
async def trigger_test_alert(
    admin_token: str = Header(..., alias="X-Admin-Token")
):
    """Trigger a test alert for monitoring validation (admin only)"""
    
    # TODO: Validate admin token and environment
    if not admin_token:
        raise HTTPException(status_code=401, detail="Admin token required")
    
    import os
    if os.getenv('ENVIRONMENT', 'development') == 'production':
        raise HTTPException(status_code=403, detail="Test endpoints disabled in production")
    
    # Create a fake high response time alert
    test_metrics = {
        'average_response_time_ms': 10000,  # 10 seconds
        'error_rate_percent': 0,
        'memory_usage_percent': 50,
        'cpu_usage_percent': 50
    }
    
    alerts = logger.alert_manager.check_performance_alerts(test_metrics)
    
    return {
        "message": "Test alert triggered successfully",
        "alerts_generated": len(alerts),
        "alerts": alerts,
        "timestamp": datetime.utcnow().isoformat()
    }