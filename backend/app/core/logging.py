"""
Logging configuration for InventorySync with graceful dependency handling
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Configuration from environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development').lower()
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_FORMAT = os.getenv('LOG_FORMAT', 'json' if ENVIRONMENT == 'production' else 'console')
LOG_DIR = Path(os.getenv('LOG_DIR', './logs'))

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Try to import optional dependencies
HAS_JSON_LOGGER = False
HAS_STRUCTLOG = False
HAS_SENTRY = False

try:
    from pythonjsonlogger import jsonlogger
    HAS_JSON_LOGGER = True
except ImportError:
    logging.warning("python-json-logger not installed. Using standard logging format.")

try:
    import structlog
    HAS_STRUCTLOG = True
except ImportError:
    logging.info("structlog not installed. Using standard logging.")

try:
    import sentry_sdk
    HAS_SENTRY = True
except ImportError:
    logging.info("sentry-sdk not installed. Sentry integration disabled.")
    HAS_SENTRY = False

# Import Sentry integrations separately to handle missing dependencies
LoggingIntegration = None
FastApiIntegration = None
SqlalchemyIntegration = None
RedisIntegration = None

if HAS_SENTRY:
    try:
        from sentry_sdk.integrations.logging import LoggingIntegration
    except (ImportError, Exception):
        pass
    
    try:
        from sentry_sdk.integrations.fastapi import FastApiIntegration
    except (ImportError, Exception):
        pass
    
    try:
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    except (ImportError, Exception):
        pass
    
    try:
        from sentry_sdk.integrations.redis import RedisIntegration
    except (ImportError, Exception):
        pass


class CustomJsonFormatter(logging.Formatter):
    """Custom JSON formatter with fallback to standard formatter if json-logger not available"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if HAS_JSON_LOGGER:
            self.json_formatter = jsonlogger.JsonFormatter()
    
    def format(self, record):
        if HAS_JSON_LOGGER:
            # Add custom fields
            record.timestamp = datetime.utcnow().isoformat()
            record.environment = ENVIRONMENT
            record.service = 'inventorysync-api'
            
            # Add correlation ID if available
            if hasattr(record, 'correlation_id'):
                record.correlation_id = record.correlation_id
            
            # Add user context if available
            if hasattr(record, 'user_id'):
                record.user_id = record.user_id
            if hasattr(record, 'store_id'):
                record.store_id = record.store_id
            
            return self.json_formatter.format(record)
        else:
            # Fallback to standard format
            return super().format(record)


class LoggingConfig:
    """Centralized logging configuration with graceful dependency handling"""
    
    @staticmethod
    def setup_sentry():
        """Configure Sentry error tracking if available"""
        if not HAS_SENTRY:
            return
        
        SENTRY_DSN = os.getenv('SENTRY_DSN')
        ENABLE_SENTRY = os.getenv('ENABLE_SENTRY', 'true').lower() == 'true'
        
        if not ENABLE_SENTRY or not SENTRY_DSN:
            return
        
        try:
            integrations = []
            
            # Add logging integration if available
            if LoggingIntegration:
                integrations.append(LoggingIntegration(level=logging.INFO, event_level=logging.ERROR))
            
            # Add optional integrations if available
            if FastApiIntegration:
                integrations.append(FastApiIntegration(transaction_style="endpoint"))
            
            if SqlalchemyIntegration:
                integrations.append(SqlalchemyIntegration())
            
            if RedisIntegration:
                integrations.append(RedisIntegration())
            
            sentry_sdk.init(
                dsn=SENTRY_DSN,
                environment=ENVIRONMENT,
                integrations=integrations,
                traces_sample_rate=0.1 if ENVIRONMENT == 'production' else 1.0,
                attach_stacktrace=True,
                send_default_pii=False,
                before_send=LoggingConfig._before_send_sentry,
                release=os.getenv('APP_VERSION', 'unknown')
            )
            logging.info("Sentry integration initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Sentry: {e}")
    
    @staticmethod
    def _before_send_sentry(event, hint):
        """Filter sensitive data before sending to Sentry"""
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
        """Configure structlog if available"""
        if not HAS_STRUCTLOG:
            return
        
        try:
            processors = [
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
            ]
            
            if LOG_FORMAT == 'json':
                processors.append(structlog.processors.JSONRenderer())
            else:
                processors.append(structlog.dev.ConsoleRenderer())
            
            structlog.configure(
                processors=processors,
                context_class=dict,
                logger_factory=structlog.stdlib.LoggerFactory(),
                cache_logger_on_first_use=True,
            )
            logging.info("structlog configured successfully")
        except Exception as e:
            logging.error(f"Failed to configure structlog: {e}")
    
    @staticmethod
    def get_formatter():
        """Get appropriate formatter based on configuration and available dependencies"""
        if LOG_FORMAT == 'json' and HAS_JSON_LOGGER:
            return CustomJsonFormatter()
        else:
            return logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
    
    @staticmethod
    def get_file_handler(log_type: str, max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5) -> logging.Handler:
        """Create rotating file handler"""
        log_file = LOG_DIR / f"{log_type}.log"
        
        try:
            handler = logging.handlers.RotatingFileHandler(
                filename=str(log_file),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            handler.setFormatter(LoggingConfig.get_formatter())
            return handler
        except Exception as e:
            logging.error(f"Failed to create file handler for {log_type}: {e}")
            # Return a null handler as fallback
            return logging.NullHandler()
    
    @staticmethod
    def setup_logging():
        """Main logging setup with graceful fallbacks"""
        # Setup Sentry first if available
        LoggingConfig.setup_sentry()
        
        # Setup structlog if available
        LoggingConfig.setup_structlog()
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
        
        # Remove existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(LoggingConfig.get_formatter())
        root_logger.addHandler(console_handler)
        
        # Try to add file handlers
        try:
            # Application log
            app_handler = LoggingConfig.get_file_handler('app')
            app_handler.setLevel(logging.DEBUG)
            root_logger.addHandler(app_handler)
        except Exception as e:
            logging.warning(f"Could not set up application file handler: {e}")
        
        try:
            # Error log
            error_handler = LoggingConfig.get_file_handler('error')
            error_handler.setLevel(logging.ERROR)
            root_logger.addHandler(error_handler)
        except Exception as e:
            logging.warning(f"Could not set up error file handler: {e}")
        
        # Reduce noise from third-party libraries
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.WARNING)
        
        logging.info(f"Logging configured - Level: {LOG_LEVEL}, Format: {LOG_FORMAT}, Environment: {ENVIRONMENT}")
        logging.info(f"Optional dependencies - JSON Logger: {HAS_JSON_LOGGER}, Structlog: {HAS_STRUCTLOG}, Sentry: {HAS_SENTRY}")


# Utility functions
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    if HAS_STRUCTLOG:
        try:
            return structlog.get_logger(name)
        except:
            pass
    
    return logging.getLogger(name)


def log_performance_metric(metric_name: str, value: float, unit: str = 'ms', tags: Optional[Dict[str, str]] = None):
    """Log a performance metric"""
    logger = get_logger('inventorysync.performance')
    logger.info(
        f"Performance metric: {metric_name}={value}{unit}",
        extra={
            'metric_name': metric_name,
            'value': value,
            'unit': unit,
            'tags': tags or {}
        }
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
        f"Audit event: {action} on {resource_type}/{resource_id} by user {user_id}",
        extra={
            'action': action,
            'user_id': user_id,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'changes': changes,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': datetime.utcnow().isoformat()
        }
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
        f"Security event: {event_type} (severity: {severity})",
        extra={
            'event_type': event_type,
            'severity': severity,
            'user_id': user_id,
            'ip_address': ip_address,
            'details': details or {},
            'timestamp': datetime.utcnow().isoformat()
        }
    )


# Initialize logging on import
try:
    LoggingConfig.setup_logging()
except Exception as e:
    # Fallback to basic logging if setup fails
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logging.error(f"Failed to setup logging configuration: {e}")
