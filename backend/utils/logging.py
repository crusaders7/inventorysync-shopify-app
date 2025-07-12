"""
Simplified logging setup for InventorySync
"""

import logging
import sys

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('inventorysync.log')
    ]
)

logger = logging.getLogger('inventorysync')

# Add missing methods to logger for compatibility
def security_event(event_type, **kwargs):
    """Log security events"""
    logger.warning(f"Security event: {event_type}", extra=kwargs)

def api_request(method, path, status_code, response_time, client_ip=None):
    """Log API requests"""
    logger.info(f"API: {method} {path} - {status_code} ({response_time:.3f}s)")

def get_performance_metrics():
    """Get mock performance metrics"""
    return {
        "monitoring": "disabled",
        "uptime_seconds": 3600,
        "average_response_time_ms": 150,
        "error_rate_percent": 0.1,
        "memory_usage_percent": 45.0,
        "cpu_usage_percent": 20.0,
        "total_requests": 1000,
        "total_errors": 1,
        "active_alerts": [],
        "recent_alerts": []
    }

# Add methods to logger instance
logger.security_event = security_event
logger.api_request = api_request
logger.get_performance_metrics = get_performance_metrics

def get_logger(name: str = None):
    """Get logger instance"""
    if name:
        return logging.getLogger(f'inventorysync.{name}')
    return logger