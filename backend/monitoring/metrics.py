"""Prometheus metrics for monitoring"""

from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from functools import wraps
import time
import psutil
import asyncio
from typing import Callable

# Define metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_connections = Gauge(
    'active_connections',
    'Number of active connections'
)

database_connections_active = Gauge(
    'database_connections_active',
    'Number of active database connections'
)

database_query_duration_seconds = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type']
)

cache_hits = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

inventory_updates_total = Counter(
    'inventory_updates_total',
    'Total inventory updates',
    ['update_type']
)

alerts_created_total = Counter(
    'alerts_created_total',
    'Total alerts created',
    ['alert_type', 'priority']
)

webhook_requests_total = Counter(
    'webhook_requests_total',
    'Total webhook requests',
    ['webhook_type', 'status']
)

system_cpu_usage = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage'
)

system_memory_usage = Gauge(
    'system_memory_usage_percent',
    'System memory usage percentage'
)

app_info = Info('app_info', 'Application information')
app_info.info({
    'version': '1.0.0',
    'environment': 'production'
})

def track_request_metrics(func: Callable) -> Callable:
    """Decorator to track HTTP request metrics"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            response = await func(*args, **kwargs)
            status = response.status_code if hasattr(response, 'status_code') else 200
        except Exception as e:
            status = 500
            raise
        finally:
            duration = time.time() - start_time
            
            # Extract endpoint and method from request
            request = kwargs.get('request')
            if request:
                method = request.method
                endpoint = request.url.path
            else:
                method = 'UNKNOWN'
                endpoint = 'UNKNOWN'
            
            # Record metrics
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=str(status)
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
        
        return response
    
    return wrapper

def track_database_query(query_type: str):
    """Decorator to track database query metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                database_query_duration_seconds.labels(
                    query_type=query_type
                ).observe(duration)
        
        return wrapper
    return decorator

async def collect_system_metrics():
    """Collect system metrics periodically"""
    while True:
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            system_cpu_usage.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            system_memory_usage.set(memory.percent)
            
            # Database connections (this would need actual DB pool stats)
            # database_connections_active.set(db_pool.size())
            
        except Exception as e:
            print(f"Error collecting system metrics: {e}")
        
        await asyncio.sleep(10)  # Collect every 10 seconds

def track_cache_operation(cache_type: str, hit: bool):
    """Track cache hit/miss"""
    if hit:
        cache_hits.labels(cache_type=cache_type).inc()
    else:
        cache_misses.labels(cache_type=cache_type).inc()

def track_inventory_update(update_type: str):
    """Track inventory updates"""
    inventory_updates_total.labels(update_type=update_type).inc()

def track_alert_created(alert_type: str, priority: str):
    """Track alert creation"""
    alerts_created_total.labels(
        alert_type=alert_type,
        priority=priority
    ).inc()

def track_webhook_request(webhook_type: str, status: str):
    """Track webhook requests"""
    webhook_requests_total.labels(
        webhook_type=webhook_type,
        status=status
    ).inc()

async def metrics_endpoint() -> Response:
    """Endpoint to expose Prometheus metrics"""
    metrics = generate_latest()
    return Response(
        content=metrics,
        media_type=CONTENT_TYPE_LATEST
    )

# Start system metrics collection task
def start_metrics_collection():
    """Start background metrics collection"""
    asyncio.create_task(collect_system_metrics())
