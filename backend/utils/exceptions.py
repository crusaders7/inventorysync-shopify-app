"""
Custom exceptions for InventorySync application
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class InventorySyncException(Exception):
    """Base exception for InventorySync application"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(InventorySyncException):
    """Raised when input validation fails"""
    pass


class AuthenticationException(InventorySyncException):
    """Raised when authentication fails"""
    pass


class AuthorizationException(InventorySyncException):
    """Raised when authorization fails"""
    pass


class ShopifyAPIException(InventorySyncException):
    """Raised when Shopify API calls fail"""
    pass


class DatabaseException(InventorySyncException):
    """Raised when database operations fail"""
    pass


class InventoryException(InventorySyncException):
    """Raised when inventory operations fail"""
    pass


class ForecastingException(InventorySyncException):
    """Raised when forecasting operations fail"""
    pass


# HTTP Exception helpers
def create_http_exception(
    status_code: int,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """Create a standardized HTTP exception"""
    return HTTPException(
        status_code=status_code,
        detail={
            "error": message,
            "details": details or {},
            "type": "application_error"
        }
    )


def validation_error(message: str, field: Optional[str] = None) -> HTTPException:
    """Create a validation error response"""
    details = {"field": field} if field else {}
    return create_http_exception(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        message,
        details
    )


def unauthorized_error(message: str = "Authentication required") -> HTTPException:
    """Create an unauthorized error response"""
    return create_http_exception(status.HTTP_401_UNAUTHORIZED, message)


def forbidden_error(message: str = "Access forbidden") -> HTTPException:
    """Create a forbidden error response"""
    return create_http_exception(status.HTTP_403_FORBIDDEN, message)


def not_found_error(resource: str, identifier: Optional[str] = None) -> HTTPException:
    """Create a not found error response"""
    message = f"{resource} not found"
    if identifier:
        message += f": {identifier}"
    return create_http_exception(status.HTTP_404_NOT_FOUND, message)


def conflict_error(message: str) -> HTTPException:
    """Create a conflict error response"""
    return create_http_exception(status.HTTP_409_CONFLICT, message)


def internal_server_error(message: str = "Internal server error") -> HTTPException:
    """Create an internal server error response"""
    return create_http_exception(status.HTTP_500_INTERNAL_SERVER_ERROR, message)