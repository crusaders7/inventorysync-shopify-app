"""
Comprehensive validation utilities for InventorySync
Enhanced validation with security, data integrity, and business logic checks
"""

import re
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from pydantic import BaseModel, validator
from fastapi import HTTPException
from .exceptions import validation_error


class ShopDomainValidator:
    """Validator for Shopify shop domains"""
    
    @staticmethod
    def validate(domain: str) -> str:
        """Validate and normalize shop domain"""
        if not domain:
            raise ValueError("Shop domain is required")
        
        # Remove protocol if present
        domain = domain.replace('https://', '').replace('http://', '')
        
        # Ensure .myshopify.com suffix
        if not domain.endswith('.myshopify.com'):
            if '.' in domain:
                raise ValueError("Invalid shop domain format")
            domain = f"{domain}.myshopify.com"
        
        # Extract shop name
        shop_name = domain.replace('.myshopify.com', '')
        
        # Validate shop name format
        if not re.match(r'^[a-z0-9-]{3,60}$', shop_name):
            raise ValueError(
                "Shop name must be 3-60 characters long and contain only "
                "lowercase letters, numbers, and hyphens"
            )
        
        return domain


class SKUValidator:
    """Validator for product SKUs"""
    
    @staticmethod
    def validate(sku: str) -> str:
        """Validate SKU format"""
        if not sku:
            raise ValueError("SKU is required")
        
        # Remove whitespace
        sku = sku.strip().upper()
        
        # Check length
        if len(sku) < 2 or len(sku) > 50:
            raise ValueError("SKU must be between 2 and 50 characters")
        
        # Check format (alphanumeric, hyphens, underscores)
        if not re.match(r'^[A-Z0-9_-]+$', sku):
            raise ValueError(
                "SKU can only contain uppercase letters, numbers, "
                "hyphens, and underscores"
            )
        
        return sku


class StockValidator:
    """Validator for stock quantities"""
    
    @staticmethod
    def validate_quantity(quantity: int) -> int:
        """Validate stock quantity"""
        if not isinstance(quantity, int):
            raise ValueError("Quantity must be an integer")
        
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        
        if quantity > 1000000:
            raise ValueError("Quantity cannot exceed 1,000,000")
        
        return quantity
    
    @staticmethod
    def validate_reorder_point(reorder_point: int) -> int:
        """Validate reorder point"""
        if not isinstance(reorder_point, int):
            raise ValueError("Reorder point must be an integer")
        
        if reorder_point < 0:
            raise ValueError("Reorder point cannot be negative")
        
        if reorder_point > 100000:
            raise ValueError("Reorder point cannot exceed 100,000")
        
        return reorder_point


class ProductValidator:
    """Validator for product data"""
    
    @staticmethod
    def validate_name(name: str) -> str:
        """Validate product name"""
        if not name:
            raise ValueError("Product name is required")
        
        name = name.strip()
        
        if len(name) < 2:
            raise ValueError("Product name must be at least 2 characters")
        
        if len(name) > 200:
            raise ValueError("Product name cannot exceed 200 characters")
        
        # Check for invalid characters
        if re.search(r'[<>"\']', name):
            raise ValueError("Product name contains invalid characters")
        
        return name
    
    @staticmethod
    def validate_location(location: str) -> str:
        """Validate location name"""
        if not location:
            raise ValueError("Location is required")
        
        location = location.strip()
        
        if len(location) < 2:
            raise ValueError("Location must be at least 2 characters")
        
        if len(location) > 100:
            raise ValueError("Location cannot exceed 100 characters")
        
        return location


class AlertValidator:
    """Validator for alert data"""
    
    VALID_SEVERITIES = ['info', 'warning', 'critical']
    VALID_STATUSES = ['active', 'resolved', 'dismissed']
    
    @staticmethod
    def validate_severity(severity: str) -> str:
        """Validate alert severity"""
        if severity not in AlertValidator.VALID_SEVERITIES:
            raise ValueError(f"Severity must be one of: {AlertValidator.VALID_SEVERITIES}")
        return severity
    
    @staticmethod
    def validate_status(status: str) -> str:
        """Validate alert status"""
        if status not in AlertValidator.VALID_STATUSES:
            raise ValueError(f"Status must be one of: {AlertValidator.VALID_STATUSES}")
        return status


class APIKeyValidator:
    """Validator for API keys and secrets"""
    
    @staticmethod
    def validate_api_key(api_key: str) -> str:
        """Validate Shopify API key format"""
        if not api_key:
            raise ValueError("API key is required")
        
        # Shopify API keys are typically 32 character hex strings
        if not re.match(r'^[a-f0-9]{32}$', api_key):
            raise ValueError("Invalid API key format")
        
        return api_key
    
    @staticmethod
    def validate_api_secret(api_secret: str) -> str:
        """Validate Shopify API secret format"""
        if not api_secret:
            raise ValueError("API secret is required")
        
        # Shopify API secrets are typically 32+ character hex strings
        if len(api_secret) < 32 or not re.match(r'^[a-f0-9]+$', api_secret):
            raise ValueError("Invalid API secret format")
        
        return api_secret


def validate_request_data(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
    """Validate request data has required fields"""
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required fields: {', '.join(missing_fields)}"
        )
    
    return data


def sanitize_string(value: str, max_length: int = None) -> str:
    """Sanitize string input"""
    if not isinstance(value, str):
        raise ValueError("Value must be a string")
    
    # Strip whitespace
    value = value.strip()
    
    # Remove potentially dangerous characters
    value = re.sub(r'[<>"\'\x00-\x1f\x7f-\x9f]', '', value)
    
    # Check length
    if max_length and len(value) > max_length:
        raise ValueError(f"Value cannot exceed {max_length} characters")
    
    return value


def validate_pagination(page: int = 1, limit: int = 20) -> tuple[int, int]:
    """Validate pagination parameters"""
    if page < 1:
        raise validation_error("Page must be 1 or greater")
    
    if limit < 1 or limit > 100:
        raise validation_error("Limit must be between 1 and 100")
    
    return page, limit


def validate_sort_params(sort_by: str, sort_order: str = "asc") -> tuple[str, str]:
    """Validate sorting parameters"""
    valid_sort_fields = [
        'id', 'product_name', 'sku', 'current_stock', 'reorder_point', 
        'created_at', 'updated_at', 'location'
    ]
    
    if sort_by not in valid_sort_fields:
        raise validation_error(f"Invalid sort field. Must be one of: {valid_sort_fields}")
    
    if sort_order.lower() not in ['asc', 'desc']:
        raise validation_error("Sort order must be 'asc' or 'desc'")
    
    return sort_by, sort_order.lower()


# =============================================================================
# ENHANCED VALIDATION CLASSES
# =============================================================================

class ValidationError(Exception):
    """Enhanced validation error with field-specific details"""
    
    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value
        super().__init__(f"{field}: {message}")


class EnhancedShopifyValidator:
    """Enhanced Shopify domain validation with security checks"""
    
    SHOPIFY_DOMAIN_PATTERN = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9\-]*\.myshopify\.com$')
    BLOCKED_DOMAINS = {'test', 'demo', 'admin', 'api', 'staging', 'development'}
    
    @classmethod
    def validate_domain(cls, domain: str) -> str:
        """Enhanced domain validation with security checks"""
        if not domain:
            raise ValidationError("shop_domain", "Shop domain is required")
        
        domain = domain.strip().lower()
        
        # Remove protocol if present
        domain = domain.replace('https://', '').replace('http://', '')
        
        if not cls.SHOPIFY_DOMAIN_PATTERN.match(domain):
            raise ValidationError(
                "shop_domain", 
                "Invalid Shopify domain format. Must be like 'store-name.myshopify.com'"
            )
        
        # Extract shop name for additional checks
        shop_name = domain.split('.')[0]
        
        if len(shop_name) < 3:
            raise ValidationError("shop_domain", "Shop name too short (minimum 3 characters)")
        
        if shop_name in cls.BLOCKED_DOMAINS:
            raise ValidationError("shop_domain", f"'{shop_name}' is a reserved domain name")
        
        # Check for suspicious patterns
        if '--' in shop_name or shop_name.startswith('-') or shop_name.endswith('-'):
            raise ValidationError("shop_domain", "Invalid shop name format")
        
        return domain


class CustomFieldValidator:
    """Enhanced custom field validation with type safety and security"""
    
    FIELD_NAME_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')
    RESERVED_NAMES = {
        'id', 'created_at', 'updated_at', 'store_id', 'shopify_id',
        'class', 'type', 'name', 'value', 'data', 'json', 'sql',
        'password', 'token', 'secret', 'key', 'admin', 'system'
    }
    
    FIELD_TYPES = {
        'text': {'max_length': 1000},
        'number': {'min_value': -999999999, 'max_value': 999999999},
        'integer': {'min_value': -2147483648, 'max_value': 2147483647},
        'float': {'precision': 10},
        'date': {},
        'datetime': {},
        'boolean': {},
        'select': {'max_options': 100},
        'multi_select': {'max_options': 100, 'max_selections': 20},
        'url': {},
        'email': {},
        'phone': {},
        'color': {}
    }
    
    @classmethod
    def validate_field_definition(cls, field_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate complete custom field definition"""
        
        # Validate field name
        field_name = field_data.get('field_name', '').strip().lower()
        if not cls.FIELD_NAME_PATTERN.match(field_name):
            raise ValidationError(
                "field_name",
                "Field name must start with letter and contain only lowercase letters, numbers, and underscores"
            )
        
        if len(field_name) > 50:
            raise ValidationError("field_name", "Field name too long (max 50 characters)")
        
        if field_name in cls.RESERVED_NAMES:
            raise ValidationError("field_name", f"'{field_name}' is a reserved name")
        
        # Validate field type
        field_type = field_data.get('field_type')
        if field_type not in cls.FIELD_TYPES:
            raise ValidationError(
                "field_type",
                f"Invalid field type. Must be one of: {', '.join(cls.FIELD_TYPES.keys())}"
            )
        
        # Validate display name
        display_name = field_data.get('display_name', '').strip()
        if not display_name:
            raise ValidationError("display_name", "Display name is required")
        
        if len(display_name) > 100:
            raise ValidationError("display_name", "Display name too long (max 100 characters)")
        
        # Validate target entity
        valid_entities = {'product', 'variant', 'inventory_item', 'supplier'}
        target_entity = field_data.get('target_entity')
        if target_entity not in valid_entities:
            raise ValidationError(
                "target_entity",
                f"Invalid target entity. Must be one of: {', '.join(valid_entities)}"
            )
        
        # Validate validation rules
        validation_rules = field_data.get('validation_rules', {})
        if validation_rules:
            cls._validate_field_rules(field_type, validation_rules)
        
        return field_data
    
    @classmethod
    def _validate_field_rules(cls, field_type: str, rules: Dict[str, Any]):
        """Validate field-specific validation rules"""
        
        if field_type == 'select' or field_type == 'multi_select':
            options = rules.get('options', [])
            if not isinstance(options, list):
                raise ValidationError("validation_rules.options", "Options must be a list")
            
            if len(options) > cls.FIELD_TYPES[field_type]['max_options']:
                raise ValidationError("validation_rules.options", f"Too many options (max {cls.FIELD_TYPES[field_type]['max_options']})")
            
            # Check for duplicate options
            if len(options) != len(set(options)):
                raise ValidationError("validation_rules.options", "Duplicate options not allowed")
        
        elif field_type in ['text']:
            max_length = rules.get('max_length')
            if max_length is not None:
                if not isinstance(max_length, int) or max_length < 1 or max_length > cls.FIELD_TYPES['text']['max_length']:
                    raise ValidationError("validation_rules.max_length", f"Max length must be between 1 and {cls.FIELD_TYPES['text']['max_length']}")
        
        elif field_type in ['number', 'integer', 'float']:
            min_value = rules.get('min_value')
            max_value = rules.get('max_value')
            
            if min_value is not None and max_value is not None:
                if min_value >= max_value:
                    raise ValidationError("validation_rules", "min_value must be less than max_value")


class WorkflowValidator:
    """Enhanced workflow validation with security and performance checks"""
    
    VALID_OPERATORS = {
        'equals', 'not_equals', 'greater_than', 'less_than', 
        'greater_than_or_equal', 'less_than_or_equal', 'contains', 
        'not_contains', 'starts_with', 'ends_with', 'in', 'not_in',
        'is_empty', 'is_not_empty'
    }
    
    VALID_ACTION_TYPES = {
        'create_alert', 'update_field', 'send_webhook', 'send_email',
        'update_inventory', 'send_notification'
    }
    
    BLOCKED_WEBHOOK_DOMAINS = {
        'localhost', '127.0.0.1', '0.0.0.0', '::1',
        'metadata.google.internal', '169.254.169.254'
    }
    
    @classmethod
    def validate_workflow_rule(cls, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate complete workflow rule"""
        
        # Validate rule name
        rule_name = rule_data.get('rule_name', '').strip()
        if not rule_name:
            raise ValidationError("rule_name", "Rule name is required")
        
        if len(rule_name) > 100:
            raise ValidationError("rule_name", "Rule name too long (max 100 characters)")
        
        # Validate trigger event
        valid_events = {
            'inventory_low', 'custom_field_change', 'product_created', 
            'variant_low_stock', 'daily_schedule', 'manual'
        }
        trigger_event = rule_data.get('trigger_event')
        if trigger_event not in valid_events:
            raise ValidationError(
                "trigger_event",
                f"Invalid trigger event. Must be one of: {', '.join(valid_events)}"
            )
        
        # Validate conditions
        conditions = rule_data.get('trigger_conditions', {})
        if conditions:
            cls._validate_conditions(conditions)
        
        # Validate actions
        actions = rule_data.get('actions', [])
        if not actions:
            raise ValidationError("actions", "At least one action is required")
        
        if len(actions) > 20:
            raise ValidationError("actions", "Too many actions (max 20)")
        
        for i, action in enumerate(actions):
            try:
                cls._validate_action(action)
            except ValidationError as e:
                raise ValidationError(f"actions[{i}]", e.message)
        
        # Validate priority and limits
        priority = rule_data.get('priority', 100)
        if not isinstance(priority, int) or priority < 1 or priority > 1000:
            raise ValidationError("priority", "Priority must be between 1 and 1000")
        
        max_executions = rule_data.get('max_executions_per_hour', 60)
        if not isinstance(max_executions, int) or max_executions < 0 or max_executions > 3600:
            raise ValidationError("max_executions_per_hour", "Max executions must be between 0 and 3600")
        
        return rule_data
    
    @classmethod
    def _validate_conditions(cls, conditions: Dict[str, Any]):
        """Validate workflow conditions recursively"""
        
        if not isinstance(conditions, dict):
            raise ValidationError("trigger_conditions", "Conditions must be an object")
        
        condition_type = conditions.get('type', 'and')
        if condition_type not in ['and', 'or']:
            # Single condition
            cls._validate_single_condition(conditions)
            return
        
        # Multiple conditions
        condition_list = conditions.get('conditions', [])
        if not isinstance(condition_list, list):
            raise ValidationError("trigger_conditions", "Conditions must be a list")
        
        if len(condition_list) > 50:
            raise ValidationError("trigger_conditions", "Too many conditions (max 50)")
        
        for i, condition in enumerate(condition_list):
            try:
                if isinstance(condition, dict) and condition.get('type') in ['and', 'or']:
                    cls._validate_conditions(condition)  # Recursive validation
                else:
                    cls._validate_single_condition(condition)
            except ValidationError as e:
                raise ValidationError(f"trigger_conditions.conditions[{i}]", e.message)
    
    @classmethod
    def _validate_single_condition(cls, condition: Dict[str, Any]):
        """Validate a single condition"""
        
        if not isinstance(condition, dict):
            raise ValidationError("condition", "Condition must be an object")
        
        field = condition.get('field')
        if not field or not isinstance(field, str):
            raise ValidationError("condition.field", "Field is required and must be a string")
        
        operator = condition.get('operator')
        if operator not in cls.VALID_OPERATORS:
            raise ValidationError(
                "condition.operator",
                f"Invalid operator. Must be one of: {', '.join(cls.VALID_OPERATORS)}"
            )
        
        # Value validation depends on operator
        if operator not in ['is_empty', 'is_not_empty']:
            if 'value' not in condition:
                raise ValidationError("condition.value", "Value is required for this operator")
    
    @classmethod
    def _validate_action(cls, action: Dict[str, Any]):
        """Validate a single action with security checks"""
        
        if not isinstance(action, dict):
            raise ValidationError("action", "Action must be an object")
        
        action_type = action.get('type')
        if action_type not in cls.VALID_ACTION_TYPES:
            raise ValidationError(
                "action.type",
                f"Invalid action type. Must be one of: {', '.join(cls.VALID_ACTION_TYPES)}"
            )
        
        # Type-specific validation
        if action_type == 'create_alert':
            message = action.get('message', '').strip()
            if not message:
                raise ValidationError("action.message", "Message is required for create_alert action")
            
            if len(message) > 2000:
                raise ValidationError("action.message", "Message too long (max 2000 characters)")
        
        elif action_type == 'send_webhook':
            url = action.get('url', '').strip()
            if not url:
                raise ValidationError("action.url", "URL is required for send_webhook action")
            
            # Security check for webhook URL
            cls._validate_webhook_url(url)
        
        elif action_type == 'send_email':
            to_email = action.get('to_email', '').strip()
            if not to_email:
                raise ValidationError("action.to_email", "Email is required for send_email action")
            
            # Basic email validation
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', to_email):
                raise ValidationError("action.to_email", "Invalid email format")
    
    @classmethod
    def _validate_webhook_url(cls, url: str):
        """Validate webhook URL with security checks"""
        
        import urllib.parse
        
        # Parse URL
        try:
            parsed = urllib.parse.urlparse(url)
        except Exception:
            raise ValidationError("action.url", "Invalid URL format")
        
        # Must be HTTP/HTTPS
        if parsed.scheme not in ['http', 'https']:
            raise ValidationError("action.url", "Webhook URL must use HTTP or HTTPS")
        
        # Security check - block internal/private addresses
        hostname = parsed.hostname
        if hostname in cls.BLOCKED_WEBHOOK_DOMAINS:
            raise ValidationError("action.url", "Webhook URL points to blocked domain")
        
        # Block common internal IP ranges
        if hostname:
            # Check for private IP ranges
            if (hostname.startswith('10.') or 
                hostname.startswith('172.') or 
                hostname.startswith('192.168.') or
                hostname.startswith('127.') or
                hostname == 'localhost'):
                raise ValidationError("action.url", "Webhook URL cannot point to internal networks")


class SecurityValidator:
    """Security-focused validation utilities"""
    
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>'
    ]
    
    @classmethod
    def sanitize_input(cls, value: str, max_length: int = 1000) -> str:
        """Sanitize user input for security"""
        
        if not isinstance(value, str):
            value = str(value)
        
        # Remove null bytes and control characters
        value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
        
        # Limit length
        if len(value) > max_length:
            value = value[:max_length]
        
        # Check for XSS patterns
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
                raise ValidationError("input", "Input contains potentially unsafe content")
        
        return value.strip()
    
    @classmethod
    def validate_api_key_format(cls, api_key: str) -> str:
        """Validate API key format with enhanced checks"""
        
        if not api_key:
            raise ValidationError("api_key", "API key is required")
        
        if not api_key.startswith('isk_'):
            raise ValidationError("api_key", "Invalid API key format")
        
        if len(api_key) < 20 or len(api_key) > 100:
            raise ValidationError("api_key", "Invalid API key length")
        
        # Check for valid characters (base64-like)
        key_part = api_key[4:]  # Remove 'isk_' prefix
        if not re.match(r'^[A-Za-z0-9_-]+$', key_part):
            raise ValidationError("api_key", "API key contains invalid characters")
        
        return api_key


class RateLimitValidator:
    """Rate limiting validation and enforcement"""
    
    DEFAULT_LIMITS = {
        'api_requests': 1000,  # per hour
        'webhook_calls': 500,  # per hour
        'bulk_operations': 100,  # per hour
        'report_generations': 50  # per hour
    }
    
    @classmethod
    def validate_rate_limit(cls, operation_type: str, current_count: int, limit: int = None) -> bool:
        """Check if operation is within rate limits"""
        
        if limit is None:
            limit = cls.DEFAULT_LIMITS.get(operation_type, 1000)
        
        if current_count >= limit:
            raise ValidationError(
                "rate_limit",
                f"Rate limit exceeded for {operation_type}. Limit: {limit}/hour"
            )
        
        return True


def validate_json_structure(data: Any, max_depth: int = 10, max_keys: int = 100) -> Any:
    """Validate JSON structure to prevent abuse"""
    
    def _check_depth(obj, current_depth=0):
        if current_depth > max_depth:
            raise ValidationError("json_data", f"JSON too deeply nested (max {max_depth} levels)")
        
        if isinstance(obj, dict):
            if len(obj) > max_keys:
                raise ValidationError("json_data", f"Too many keys in object (max {max_keys})")
            
            for key, value in obj.items():
                if not isinstance(key, str) or len(key) > 100:
                    raise ValidationError("json_data", "Invalid key format")
                _check_depth(value, current_depth + 1)
        
        elif isinstance(obj, list):
            if len(obj) > 1000:
                raise ValidationError("json_data", "Array too large (max 1000 items)")
            
            for item in obj:
                _check_depth(item, current_depth + 1)
        
        elif isinstance(obj, str):
            if len(obj) > 10000:
                raise ValidationError("json_data", "String value too long (max 10000 characters)")
    
    _check_depth(data)
    return data