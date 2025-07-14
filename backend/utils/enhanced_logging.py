"""
Enhanced logging configuration for InventorySync
Supports structured logging, performance metrics, and security events
"""

import logging
import sys
import os
import json
import time
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
from functools import wraps
from contextlib import contextmanager
import asyncio

# Try to import JSON logger, fallback if not available
try:
    from pythonjsonlogger import jsonlogger
    HAS_JSON_LOGGER = True
except ImportError:
    HAS_JSON_LOGGER = False

# Configuration from environment
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_FORMAT = os.getenv('LOG_FORMAT', 'json').lower()
LOG_FILE = os.getenv('LOG_FILE', 'inventorysync.log')
ENABLE_PERFORMANCE_LOGGING = os.getenv('ENABLE_PERFORMANCE_LOGGING', 'true').lower() == 'true'

class StructuredLogger:
    """Enhanced logger with structured logging support"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_handlers()
        self.performance_metrics = {
            'total_requests': 0,
            'total_errors': 0,
            'response_times': [],
            'start_time': time.time()
        }
    
    def _setup_handlers(self):
        """Setup logging handlers based on configuration"""
        self.logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
        
        # Remove existing handlers
        self.logger.handlers = []
        
        if LOG_FORMAT == 'json' and HAS_JSON_LOGGER:
            # JSON formatter for production
            handler = logging.StreamHandler(sys.stdout)
            formatter = jsonlogger.JsonFormatter(
                '%(timestamp)s %(level)s %(name)s %(message)s',
                rename_fields={'timestamp': '@timestamp', 'level': 'severity'}
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
            # File handler with JSON
            file_handler = logging.FileHandler(LOG_FILE)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        else:
            # Standard formatter for development
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            # File handler
            file_handler = logging.FileHandler(LOG_FILE)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log with additional context"""
        extra = {
            'timestamp': datetime.utcnow().isoformat(),
            'environment': os.getenv('ENVIRONMENT', 'development'),
            **kwargs
        }
        
        if LOG_FORMAT == 'json':
            # For JSON logging, add all context to the message
            log_data = {
                'message': message,
                **extra
            }
            self.logger.log(level, json.dumps(log_data))
        else:
            # For standard logging, add context as extra
            self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        if exception:
            kwargs['error_type'] = type(exception).__name__
            kwargs['error_message'] = str(exception)
            kwargs['traceback'] = traceback.format_exc()
        self._log_with_context(logging.ERROR, message, **kwargs)
        self.performance_metrics['total_errors'] += 1
    
    def critical(self, message: str, **kwargs):
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def security_event(self, event_type: str, **kwargs):
        """Log security-related events"""
        self._log_with_context(
            logging.WARNING,
            f"Security Event: {event_type}",
            event_type=event_type,
            category='security',
            **kwargs
        )
    
    def api_request(self, method: str, path: str, status_code: int, 
                    response_time: float, client_ip: Optional[str] = None, **kwargs):
        """Log API request details"""
        self.performance_metrics['total_requests'] += 1
        self.performance_metrics['response_times'].append(response_time)
        
        # Keep only last 1000 response times
        if len(self.performance_metrics['response_times']) > 1000:
            self.performance_metrics['response_times'] = \
                self.performance_metrics['response_times'][-1000:]
        
        self._log_with_context(
            logging.INFO,
            f"API Request: {method} {path}",
            method=method,
            path=path,
            status_code=status_code,
            response_time_ms=response_time * 1000,
            client_ip=client_ip,
            category='api_request',
            **kwargs
        )
    
    def database_query(self, query: str, duration: float, rows_affected: int = 0, **kwargs):
        """Log database query performance"""
        if ENABLE_PERFORMANCE_LOGGING:
            self._log_with_context(
                logging.DEBUG,
                "Database Query",
                query=query[:500],  # Truncate long queries
                duration_ms=duration * 1000,
                rows_affected=rows_affected,
                category='database',
                **kwargs
            )
    
    def cache_event(self, operation: str, key: str, hit: bool, duration: float, **kwargs):
        """Log cache operations"""
        if ENABLE_PERFORMANCE_LOGGING:
            self._log_with_context(
                logging.DEBUG,
                f"Cache {operation}",
                operation=operation,
                key=key,
                hit=hit,
                duration_ms=duration * 1000,
                category='cache',
                **kwargs
            )
    
    def background_task(self, task_name: str, status: str, duration: Optional[float] = None, **kwargs):
        """Log background task execution"""
        self._log_with_context(
            logging.INFO,
            f"Background Task: {task_name}",
            task_name=task_name,
            status=status,
            duration_ms=duration * 1000 if duration else None,
            category='background_task',
            **kwargs
        )
    
    def webhook_event(self, webhook_type: str, source: str, status: str, **kwargs):
        """Log webhook events"""
        self._log_with_context(
            logging.INFO,
            f"Webhook Event: {webhook_type}",
            webhook_type=webhook_type,
            source=source,
            status=status,
            category='webhook',
            **kwargs
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        uptime = time.time() - self.performance_metrics['start_time']
        response_times = self.performance_metrics['response_times']
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            'uptime_seconds': uptime,
            'total_requests': self.performance_metrics['total_requests'],
            'total_errors': self.performance_metrics['total_errors'],
            'error_rate_percent': (
                self.performance_metrics['total_errors'] / 
                self.performance_metrics['total_requests'] * 100
            ) if self.performance_metrics['total_requests'] > 0 else 0,
            'average_response_time_ms': avg_response_time * 1000,
            'p95_response_time_ms': (
                sorted(response_times)[int(len(response_times) * 0.95)] * 1000
            ) if response_times else 0,
            'p99_response_time_ms': (
                sorted(response_times)[int(len(response_times) * 0.99)] * 1000
            ) if response_times else 0,
        }

# Create global logger instance
logger = StructuredLogger('inventorysync')

def get_logger(name: str) -> StructuredLogger:
    """Get a logger instance for a specific module"""
    return StructuredLogger(f'inventorysync.{name}')

# Decorators for automatic logging
def log_execution_time(func):
    """Decorator to log function execution time"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug(
                f"Function executed: {func.__name__}",
                function=func.__name__,
                duration_ms=duration * 1000,
                category='performance'
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Function failed: {func.__name__}",
                function=func.__name__,
                duration_ms=duration * 1000,
                exception=e
            )
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug(
                f"Function executed: {func.__name__}",
                function=func.__name__,
                duration_ms=duration * 1000,
                category='performance'
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Function failed: {func.__name__}",
                function=func.__name__,
                duration_ms=duration * 1000,
                exception=e
            )
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper

@contextmanager
def log_context(**kwargs):
    """Context manager to add context to all logs within the block"""
    # This would require thread-local storage for full implementation
    # For now, just log entry and exit
    logger.debug("Entering context", **kwargs)
    try:
        yield
    finally:
        logger.debug("Exiting context", **kwargs)

# Structured logging helpers
def log_business_event(event_type: str, entity_type: str, entity_id: str, **details):
    """Log business-level events"""
    logger.info(
        f"Business Event: {event_type}",
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        category='business_event',
        **details
    )

def log_audit_trail(action: str, user_id: str, resource: str, **details):
    """Log audit trail for compliance"""
    logger.info(
        f"Audit Trail: {action}",
        action=action,
        user_id=user_id,
        resource=resource,
        category='audit',
        **details
    )
