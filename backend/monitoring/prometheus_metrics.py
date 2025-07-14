"""
Prometheus metrics configuration for InventorySync
Custom metrics for monitoring application performance and business metrics
"""

from prometheus_client import Counter, Histogram, Gauge, Info
from typing import Dict, Any
import time
from functools import wraps
import asyncio

# Application Info
app_info = Info('inventorysync_app', 'Application information')
app_info.info({
    'version': '1.0.0',
    'name': 'InventorySync',
    'environment': 'production'
})

# Request Metrics
http_requests_total = Counter(
    'inventorysync_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'inventorysync_http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
)

# Business Metrics
inventory_sync_total = Counter(
    'inventorysync_sync_operations_total',
    'Total inventory sync operations',
    ['store_id', 'status', 'sync_type']
)

inventory_sync_duration_seconds = Histogram(
    'inventorysync_sync_duration_seconds',
    'Inventory sync operation duration',
    ['store_id', 'sync_type'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600]
)

active_stores = Gauge(
    'inventorysync_active_stores',
    'Number of active stores'
)

total_products_tracked = Gauge(
    'inventorysync_total_products',
    'Total number of products being tracked'
)

# Queue Metrics
sync_queue_size = Gauge(
    'inventorysync_sync_queue_size',
    'Current size of sync queue',
    ['queue_type']
)

sync_queue_processing_time = Histogram(
    'inventorysync_queue_processing_seconds',
    'Time to process items from sync queue',
    ['queue_type'],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60]
)

# Error Metrics
application_errors_total = Counter(
    'inventorysync_errors_total',
    'Total application errors',
    ['error_type', 'severity', 'component']
)

webhook_errors_total = Counter(
    'inventorysync_webhook_errors_total',
    'Total webhook processing errors',
    ['webhook_type', 'error_reason']
)

# Database Metrics
database_queries_total = Counter(
    'inventorysync_database_queries_total',
    'Total database queries',
    ['query_type', 'table']
)

database_query_duration_seconds = Histogram(
    'inventorysync_database_query_duration_seconds',
    'Database query duration',
    ['query_type', 'table'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 2]
)

database_connections_active = Gauge(
    'inventorysync_database_connections_active',
    'Active database connections'
)

# Cache Metrics
cache_hits_total = Counter(
    'inventorysync_cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'inventorysync_cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

cache_evictions_total = Counter(
    'inventorysync_cache_evictions_total',
    'Total cache evictions',
    ['cache_type', 'reason']
)

# Alert Metrics
alerts_triggered_total = Counter(
    'inventorysync_alerts_triggered_total',
    'Total alerts triggered',
    ['alert_type', 'severity', 'store_id']
)

alerts_resolved_total = Counter(
    'inventorysync_alerts_resolved_total',
    'Total alerts resolved',
    ['alert_type', 'resolution_type']
)

# Custom Field Metrics
custom_fields_created_total = Counter(
    'inventorysync_custom_fields_created_total',
    'Total custom fields created',
    ['field_type', 'store_id']
)

custom_fields_active = Gauge(
    'inventorysync_custom_fields_active',
    'Number of active custom fields'
)

# Workflow Metrics
workflows_executed_total = Counter(
    'inventorysync_workflows_executed_total',
    'Total workflows executed',
    ['workflow_type', 'status', 'store_id']
)

workflow_execution_duration_seconds = Histogram(
    'inventorysync_workflow_execution_seconds',
    'Workflow execution duration',
    ['workflow_type'],
    buckets=[0.1, 0.5, 1, 5, 10, 30, 60, 300]
)

# Billing Metrics
subscription_revenue_total = Counter(
    'inventorysync_subscription_revenue_total',
    'Total subscription revenue',
    ['plan_type', 'currency']
)

active_subscriptions = Gauge(
    'inventorysync_active_subscriptions',
    'Number of active subscriptions',
    ['plan_type']
)

# Performance Metrics
api_response_time_p95 = Gauge(
    'inventorysync_api_response_time_p95_seconds',
    '95th percentile API response time'
)

api_response_time_p99 = Gauge(
    'inventorysync_api_response_time_p99_seconds',
    '99th percentile API response time'
)

# Helper functions for metric collection
def track_request_metrics(method: str, endpoint: str, status: int, duration: float):
    """Track HTTP request metrics"""
    http_requests_total.labels(method=method, endpoint=endpoint, status=str(status)).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)

def track_sync_operation(store_id: str, sync_type: str, status: str, duration: float):
    """Track inventory sync operation metrics"""
    inventory_sync_total.labels(store_id=store_id, status=status, sync_type=sync_type).inc()
    inventory_sync_duration_seconds.labels(store_id=store_id, sync_type=sync_type).observe(duration)

def track_error(error_type: str, severity: str, component: str):
    """Track application errors"""
    application_errors_total.labels(
        error_type=error_type,
        severity=severity,
        component=component
    ).inc()

def track_database_query(query_type: str, table: str, duration: float):
    """Track database query metrics"""
    database_queries_total.labels(query_type=query_type, table=table).inc()
    database_query_duration_seconds.labels(query_type=query_type, table=table).observe(duration)

def track_cache_access(cache_type: str, hit: bool):
    """Track cache access metrics"""
    if hit:
        cache_hits_total.labels(cache_type=cache_type).inc()
    else:
        cache_misses_total.labels(cache_type=cache_type).inc()

def track_alert(alert_type: str, severity: str, store_id: str, triggered: bool = True):
    """Track alert metrics"""
    if triggered:
        alerts_triggered_total.labels(
            alert_type=alert_type,
            severity=severity,
            store_id=store_id
        ).inc()
    else:
        alerts_resolved_total.labels(
            alert_type=alert_type,
            resolution_type='auto'
        ).inc()

def track_workflow_execution(workflow_type: str, status: str, store_id: str, duration: float):
    """Track workflow execution metrics"""
    workflows_executed_total.labels(
        workflow_type=workflow_type,
        status=status,
        store_id=store_id
    ).inc()
    workflow_execution_duration_seconds.labels(workflow_type=workflow_type).observe(duration)

# Decorators for automatic metric collection
def monitor_endpoint(endpoint: str):
    """Decorator to monitor FastAPI endpoints"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status = 200
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = 500
                raise
            finally:
                duration = time.time() - start_time
                track_request_metrics(
                    method=kwargs.get('request', {}).method if 'request' in kwargs else 'UNKNOWN',
                    endpoint=endpoint,
                    status=status,
                    duration=duration
                )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            status = 200
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = 500
                raise
            finally:
                duration = time.time() - start_time
                track_request_metrics(
                    method='UNKNOWN',
                    endpoint=endpoint,
                    status=status,
                    duration=duration
                )
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator

def monitor_database_operation(operation: str, table: str):
    """Decorator to monitor database operations"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                track_database_query(operation, table, duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                track_database_query(operation, table, duration)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator

# Business metrics update functions
def update_business_metrics(active_stores_count: int, total_products: int):
    """Update business-related gauge metrics"""
    active_stores.set(active_stores_count)
    total_products_tracked.set(total_products)

def update_subscription_metrics(subscriptions_by_plan: Dict[str, int]):
    """Update subscription gauge metrics"""
    for plan, count in subscriptions_by_plan.items():
        active_subscriptions.labels(plan_type=plan).set(count)

def update_queue_metrics(queue_sizes: Dict[str, int]):
    """Update queue size metrics"""
    for queue_type, size in queue_sizes.items():
        sync_queue_size.labels(queue_type=queue_type).set(size)

def update_performance_metrics(p95: float, p99: float):
    """Update API performance percentile metrics"""
    api_response_time_p95.set(p95)
    api_response_time_p99.set(p99)
