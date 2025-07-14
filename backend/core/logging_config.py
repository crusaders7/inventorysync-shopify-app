"""
Comprehensive logging configuration for InventorySync
Includes structured logging, log rotation, Sentry integration, and APM
"""

import os
import sys
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import json
import structlog
from pythonjsonlogger import jsonlogger
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration


# Configuration from environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development').lower()
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_FORMAT = os.getenv('LOG_FORMAT', 'json' if ENVIRONMENT == 'production' else 'console')
LOG_DIR = Path(os.getenv('LOG_DIR', '/var/log/inventorysync'))
SENTRY_DSN = os.getenv('SENTRY_DSN')
ENABLE_SENTRY = os.getenv('ENABLE_SENTRY', 'true').lower() == 'true'
ENABLE_APM = os.getenv('ENABLE_APM', 'true').lower() == 'true'

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['@timestamp'] = datetime.utcnow().isoformat()
        log_record['environment'] = ENVIRONMENT
        log_record['service'] = 'inventorysync-api'
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        
        # Add correlation ID if available
        if hasattr(record, 'correlation_id'):
            log_record['correlation_id'] = record.correlation_id
        
        # Add user context if available
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        if hasattr(record, 'store_id'):
            log_record['store_id'] = record.store_id


class StructuredLoggingConfig:
    """Centralized logging configuration"""
    
    @staticmethod
    def setup_sentry():
        """Configure Sentry error tracking"""
        if not ENABLE_SENTRY or not SENTRY_DSN:
            return
        
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=ENVIRONMENT,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                RedisIntegration(),
                LoggingIntegration(
                    level=logging.INFO,  # Capture info and above
                    event_level=logging.ERROR  # Send errors and above to Sentry
                )
            ],
            traces_sample_rate=0.1 if ENVIRONMENT == 'production' else 1.0,
            profiles_sample_rate=0.1 if ENVIRONMENT == 'production' else 1.0,
            attach_stacktrace=True,
            send_default_pii=False,  # Don't send personally identifiable information
            before_send=StructuredLoggingConfig._before_send_sentry,
            release=os.getenv('APP_VERSION', 'unknown')
        )
    
    @staticmethod
    def _before_send_sentry(event, hint):
        """Filter sensitive data before sending to Sentry"""
        # Remove sensitive fields
        sensitive_fields = ['password', 'token', 'secret', 'api_key', 'credit_card']
        
        def remove_sensitive(data):
            if isinstance(data, dict):
                return {
                    k: '***REDACTED***' if any(s in k.lower() for s in sensitive_fields) else remove_sensitive(v)
                    for k, v in data.items()
                }
            elif isinstance(data, list):
                return [remove_sensitive(item) for item in data]
            return data
        
        if 'request' in event:
            event['request'] = remove_sensitive(event['request'])
        
        if 'extra' in event:
            event['extra'] = remove_sensitive(event['extra'])
        
        return event
    
    @staticmethod
    def setup_structlog():
        """Configure structlog for structured logging"""
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer() if LOG_FORMAT == 'json' else structlog.dev.ConsoleRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    
    @staticmethod
    def get_file_handler(log_type: str, max_bytes: int = 100 * 1024 * 1024, backup_count: int = 10) -> logging.Handler:
        """Create rotating file handler with compression"""
        log_file = LOG_DIR / f"{log_type}.log"
        
        handler = logging.handlers.RotatingFileHandler(
            filename=str(log_file),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        if LOG_FORMAT == 'json':
            handler.setFormatter(CustomJsonFormatter())
        else:
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
        
        return handler
    
    @staticmethod
    def get_timed_rotating_handler(log_type: str, when: str = 'midnight', interval: int = 1, backup_count: int = 30) -> logging.Handler:
        """Create time-based rotating file handler"""
        log_file = LOG_DIR / f"{log_type}.log"
        
        handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(log_file),
            when=when,
            interval=interval,
            backupCount=backup_count,
            encoding='utf-8',
            utc=True
        )
        
        if LOG_FORMAT == 'json':
            handler.setFormatter(CustomJsonFormatter())
        else:
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
        
        return handler
    
    @staticmethod
    def setup_logging():
        """Main logging setup"""
        # Setup Sentry first
        StructuredLoggingConfig.setup_sentry()
        
        # Setup structlog
        StructuredLoggingConfig.setup_structlog()
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
        
        # Remove existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        if LOG_FORMAT == 'json':
            console_handler.setFormatter(CustomJsonFormatter())
        else:
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
        root_logger.addHandler(console_handler)
        
        # Application log (rotating by size)
        app_handler = StructuredLoggingConfig.get_file_handler('app')
        app_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(app_handler)
        
        # Error log (rotating daily)
        error_handler = StructuredLoggingConfig.get_timed_rotating_handler('error', when='midnight')
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)
        
        # Setup specialized loggers
        StructuredLoggingConfig._setup_specialized_loggers()
    
    @staticmethod
    def _setup_specialized_loggers():
        """Setup specialized loggers for different components"""
        
        # API access log
        api_logger = logging.getLogger('inventorysync.api')
        api_logger.handlers.clear()
        api_logger.addHandler(StructuredLoggingConfig.get_timed_rotating_handler('api_access', when='midnight'))
        api_logger.propagate = False
        
        # Security/Audit log
        security_logger = logging.getLogger('inventorysync.security')
        security_logger.handlers.clear()
        security_handler = StructuredLoggingConfig.get_timed_rotating_handler('security_audit', when='midnight', backup_count=90)
        security_handler.setLevel(logging.INFO)
        security_logger.addHandler(security_handler)
        security_logger.propagate = False
        
        # Performance log
        perf_logger = logging.getLogger('inventorysync.performance')
        perf_logger.handlers.clear()
        perf_logger.addHandler(StructuredLoggingConfig.get_file_handler('performance', max_bytes=50 * 1024 * 1024))
        perf_logger.propagate = False
        
        # Background tasks log
        task_logger = logging.getLogger('inventorysync.tasks')
        task_logger.handlers.clear()
        task_logger.addHandler(StructuredLoggingConfig.get_file_handler('background_tasks'))
        task_logger.propagate = False
        
        # Webhook log
        webhook_logger = logging.getLogger('inventorysync.webhooks')
        webhook_logger.handlers.clear()
        webhook_logger.addHandler(StructuredLoggingConfig.get_file_handler('webhooks'))
        webhook_logger.propagate = False
        
        # Reduce noise from third-party libraries
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)


class LogAggregationConfig:
    """Configuration for log aggregation (e.g., ELK stack, CloudWatch)"""
    
    @staticmethod
    def get_log_shipper_config() -> Dict[str, Any]:
        """Get configuration for log shipping to aggregation service"""
        aggregation_type = os.getenv('LOG_AGGREGATION_TYPE', 'none').lower()
        
        if aggregation_type == 'elasticsearch':
            return {
                'type': 'elasticsearch',
                'hosts': os.getenv('ELASTICSEARCH_HOSTS', 'localhost:9200').split(','),
                'index_pattern': f"inventorysync-{ENVIRONMENT}-%{{Y.m.d}}",
                'bulk_size': int(os.getenv('ES_BULK_SIZE', '1000')),
                'flush_interval': int(os.getenv('ES_FLUSH_INTERVAL', '5'))
            }
        elif aggregation_type == 'cloudwatch':
            return {
                'type': 'cloudwatch',
                'log_group': f"/aws/inventorysync/{ENVIRONMENT}",
                'region': os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
                'stream_name': os.getenv('CLOUDWATCH_STREAM_NAME', 'api')
            }
        elif aggregation_type == 'datadog':
            return {
                'type': 'datadog',
                'api_key': os.getenv('DATADOG_API_KEY'),
                'site': os.getenv('DATADOG_SITE', 'datadoghq.com'),
                'service': 'inventorysync-api',
                'source': 'python',
                'tags': [f"env:{ENVIRONMENT}"]
            }
        
        return {'type': 'none'}


# Logging utilities
def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)


def log_performance_metric(metric_name: str, value: float, unit: str = 'ms', tags: Optional[Dict[str, str]] = None):
    """Log a performance metric"""
    logger = get_logger('inventorysync.performance')
    logger.info(
        "performance_metric",
        metric_name=metric_name,
        value=value,
        unit=unit,
        tags=tags or {}
    )


def log_audit_event(
    action: str,
    user_id: str,
    resource_type: str,
    resource_id: str,
    changes: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Log an audit event for compliance"""
    logger = get_logger('inventorysync.security')
    logger.info(
        "audit_event",
        action=action,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
        timestamp=datetime.utcnow().isoformat()
    )


def log_security_event(
    event_type: str,
    severity: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """Log a security event"""
    logger = get_logger('inventorysync.security')
    log_method = getattr(logger, severity.lower(), logger.warning)
    log_method(
        "security_event",
        event_type=event_type,
        severity=severity,
        user_id=user_id,
        ip_address=ip_address,
        details=details or {},
        timestamp=datetime.utcnow().isoformat()
    )


# Initialize logging on import
StructuredLoggingConfig.setup_logging()
