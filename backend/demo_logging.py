#!/usr/bin/env python3
"""
Demonstration of the flexible logging configuration
"""

import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("InventorySync Logging Configuration Demo")
print("=" * 50)

# Import and set up logging
from app.core.logging import LoggingConfig, get_logger, log_performance_metric, log_audit_event, log_security_event

# Show current configuration
from app.core.logging import HAS_JSON_LOGGER, HAS_STRUCTLOG, HAS_SENTRY, ENVIRONMENT, LOG_LEVEL, LOG_FORMAT

print("\nCurrent Configuration:")
print(f"  Environment: {ENVIRONMENT}")
print(f"  Log Level: {LOG_LEVEL}")
print(f"  Log Format: {LOG_FORMAT}")
print(f"  JSON Logger Available: {HAS_JSON_LOGGER}")
print(f"  Structlog Available: {HAS_STRUCTLOG}")
print(f"  Sentry Available: {HAS_SENTRY}")

print("\n" + "-" * 50)
print("Demo: Basic Logging")
print("-" * 50)

# Get a logger for our demo
logger = get_logger('demo')

# Show different log levels
logger.debug("This is a debug message - useful for development")
logger.info("This is an info message - general information")
logger.warning("This is a warning - something to pay attention to")
logger.error("This is an error - something went wrong")

# You can also log with additional context
logger.info("User logged in", extra={"user_id": "12345", "ip": "192.168.1.1"})

print("\n" + "-" * 50)
print("Demo: Performance Monitoring")
print("-" * 50)

# Log performance metrics
log_performance_metric('api_response_time', 145.23, 'ms', {'endpoint': '/api/products'})
log_performance_metric('database_query_time', 23.5, 'ms', {'query': 'get_user_by_id'})
log_performance_metric('cache_hit_rate', 0.85, 'ratio', {'cache': 'redis'})

print("\n" + "-" * 50)
print("Demo: Audit Logging")
print("-" * 50)

# Log audit events for compliance
log_audit_event(
    action='update_inventory',
    user_id='user_123',
    resource_type='product',
    resource_id='prod_456',
    changes={'quantity': {'old': 100, 'new': 85}},
    ip_address='192.168.1.100',
    user_agent='Mozilla/5.0...'
)

log_audit_event(
    action='create_webhook',
    user_id='admin_001',
    resource_type='webhook',
    resource_id='webhook_789',
    changes={'url': 'https://example.com/webhook'},
    ip_address='10.0.0.5'
)

print("\n" + "-" * 50)
print("Demo: Security Event Logging")
print("-" * 50)

# Log security events
log_security_event(
    event_type='failed_login_attempt',
    severity='warning',
    user_id='unknown',
    ip_address='192.168.1.50',
    details={'attempts': 3, 'username': 'admin'}
)

log_security_event(
    event_type='api_rate_limit_exceeded',
    severity='error',
    user_id='user_789',
    ip_address='203.0.113.5',
    details={'limit': 100, 'window': '1h', 'requests': 150}
)

log_security_event(
    event_type='suspicious_activity',
    severity='critical',
    user_id='user_456',
    ip_address='198.51.100.42',
    details={'activity': 'multiple_store_access', 'stores_accessed': 10}
)

print("\n" + "-" * 50)
print("Demo: Structured Logging for Different Components")
print("-" * 50)

# Get loggers for different components
api_logger = get_logger('inventorysync.api')
sync_logger = get_logger('inventorysync.sync')
webhook_logger = get_logger('inventorysync.webhooks')

# API logging
api_logger.info("API request processed", extra={
    'method': 'POST',
    'path': '/api/products',
    'status_code': 201,
    'response_time_ms': 156,
    'user_id': 'user_123'
})

# Sync logging
sync_logger.info("Inventory sync started", extra={
    'store_id': 'store_456',
    'products_count': 1500,
    'sync_type': 'full'
})

sync_logger.warning("Sync rate limited", extra={
    'store_id': 'store_456',
    'retry_after': 60,
    'remaining_items': 500
})

# Webhook logging
webhook_logger.info("Webhook received", extra={
    'topic': 'products/update',
    'shop': 'example.myshopify.com',
    'webhook_id': 'webhook_123'
})

webhook_logger.error("Webhook processing failed", extra={
    'topic': 'products/update',
    'error': 'Invalid payload',
    'retry_count': 2
})

print("\n" + "=" * 50)
print("Demo completed!")
print("\nKey Features:")
print("  ✓ Works with or without python-json-logger")
print("  ✓ Works with or without structlog")
print("  ✓ Works with or without sentry-sdk")
print("  ✓ Provides consistent API regardless of available dependencies")
print("  ✓ Automatically creates log directories")
print("  ✓ Supports file rotation")
print("  ✓ Configurable via environment variables")
print("  ✓ Includes security and audit logging utilities")
