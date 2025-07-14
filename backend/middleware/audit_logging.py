"""
Audit logging middleware for tracking sensitive operations
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, List, Dict, Any, Optional
import json
import time
from core.logging_config import log_audit_event, get_logger

logger = get_logger('inventorysync.audit')


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging sensitive operations for compliance"""
    
    # Define sensitive operations that require audit logging
    AUDIT_PATHS = {
        # User management
        ("POST", "/api/v1/auth/login"): "user_login",
        ("POST", "/api/v1/auth/logout"): "user_logout",
        ("POST", "/api/v1/auth/register"): "user_registration",
        ("PUT", "/api/v1/users/{user_id}"): "user_update",
        ("DELETE", "/api/v1/users/{user_id}"): "user_delete",
        
        # Billing operations
        ("POST", "/api/v1/billing/subscribe"): "subscription_create",
        ("PUT", "/api/v1/billing/subscription"): "subscription_update",
        ("DELETE", "/api/v1/billing/subscription"): "subscription_cancel",
        
        # Inventory modifications
        ("PUT", "/api/v1/inventory/{product_id}"): "inventory_update",
        ("POST", "/api/v1/inventory/bulk-update"): "inventory_bulk_update",
        
        # Configuration changes
        ("PUT", "/api/v1/settings"): "settings_update",
        ("PUT", "/api/v1/integrations"): "integration_update",
        
        # Data export/import
        ("GET", "/api/v1/export"): "data_export",
        ("POST", "/api/v1/import"): "data_import",
        
        # Webhook management
        ("POST", "/api/v1/webhooks"): "webhook_create",
        ("DELETE", "/api/v1/webhooks/{webhook_id}"): "webhook_delete",
        
        # GDPR operations
        ("GET", "/api/v1/gdpr/export"): "gdpr_data_export",
        ("DELETE", "/api/v1/gdpr/delete"): "gdpr_data_delete",
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log audit events for sensitive operations"""
        start_time = time.time()
        
        # Check if this is an auditable operation
        path_pattern = self._match_path_pattern(request.method, request.url.path)
        if not path_pattern:
            return await call_next(request)
        
        # Get user context
        user_id = None
        store_id = None
        if hasattr(request.state, "user"):
            user_id = getattr(request.state.user, "id", None)
            store_id = getattr(request.state.user, "store_id", None)
        
        # Get client info
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Capture request body for certain operations
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                request_body = json.loads(body) if body else None
                # Recreate request with body
                request._body = body
            except:
                pass
        
        # Get action type
        action = self.AUDIT_PATHS.get(path_pattern, "unknown")
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        duration = time.time() - start_time
        
        # Prepare audit details
        details = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "status_code": response.status_code,
            "duration_ms": duration * 1000,
            "success": 200 <= response.status_code < 400
        }
        
        # Add request body for certain operations (excluding sensitive fields)
        if request_body and action in ["settings_update", "integration_update"]:
            details["changes"] = self._sanitize_request_body(request_body)
        
        # Extract resource ID from path
        resource_id = self._extract_resource_id(request.url.path)
        
        # Log audit event
        log_audit_event(
            action=action,
            user_id=user_id or "anonymous",
            resource_type=self._get_resource_type(action),
            resource_id=resource_id or request.url.path,
            changes=details.get("changes"),
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return response
    
    def _match_path_pattern(self, method: str, path: str) -> Optional[tuple]:
        """Match request path against audit patterns"""
        for pattern, _ in self.AUDIT_PATHS.items():
            pattern_method, pattern_path = pattern
            if method != pattern_method:
                continue
            
            # Simple pattern matching (could be enhanced with regex)
            if self._paths_match(pattern_path, path):
                return pattern
        
        return None
    
    def _paths_match(self, pattern: str, path: str) -> bool:
        """Check if path matches pattern with placeholders"""
        pattern_parts = pattern.split("/")
        path_parts = path.split("/")
        
        if len(pattern_parts) != len(path_parts):
            return False
        
        for pattern_part, path_part in zip(pattern_parts, path_parts):
            if pattern_part.startswith("{") and pattern_part.endswith("}"):
                # This is a placeholder, any value matches
                continue
            elif pattern_part != path_part:
                return False
        
        return True
    
    def _extract_resource_id(self, path: str) -> Optional[str]:
        """Extract resource ID from path"""
        parts = path.split("/")
        # Look for UUIDs or numeric IDs in the path
        for part in parts:
            if part.replace("-", "").isalnum() and len(part) > 10:
                return part
            elif part.isdigit():
                return part
        return None
    
    def _get_resource_type(self, action: str) -> str:
        """Get resource type from action"""
        if "user" in action:
            return "user"
        elif "subscription" in action or "billing" in action:
            return "subscription"
        elif "inventory" in action:
            return "inventory"
        elif "settings" in action:
            return "settings"
        elif "integration" in action:
            return "integration"
        elif "webhook" in action:
            return "webhook"
        elif "gdpr" in action:
            return "user_data"
        else:
            return "unknown"
    
    def _sanitize_request_body(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive fields from request body"""
        if not isinstance(body, dict):
            return {}
        
        sensitive_fields = {
            "password", "token", "secret", "api_key", "private_key",
            "credit_card", "card_number", "cvv", "ssn"
        }
        
        sanitized = {}
        for key, value in body.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_request_body(value)
            else:
                sanitized[key] = value
        
        return sanitized
