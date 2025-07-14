"""Security middleware for FastAPI"""

from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
import hashlib
import secrets
from typing import Callable
from config import settings

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HSTS header for production
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # CSP header for production - more restrictive
        if settings.environment == "production":
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' https://cdn.shopify.com",
                "style-src 'self' https://cdn.shopify.com",
                "img-src 'self' data: https: blob:",
                "font-src 'self' data: https://cdn.shopify.com",
                "connect-src 'self' https://api.shopify.com wss:",
                "frame-ancestors https://*.myshopify.com https://admin.shopify.com",
                "base-uri 'self'",
                "form-action 'self'",
                "upgrade-insecure-requests"
            ]
        else:
            # Development CSP - less restrictive
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.shopify.com",
                "style-src 'self' 'unsafe-inline' https://cdn.shopify.com",
                "img-src 'self' data: https: blob:",
                "font-src 'self' data: https://cdn.shopify.com",
                "connect-src 'self' https://api.shopify.com wss: http://localhost:*",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'"
            ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        return response


class NonceMiddleware(BaseHTTPMiddleware):
    """Add nonce for CSP inline scripts"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate nonce
        nonce = secrets.token_urlsafe(16)
        request.state.nonce = nonce
        
        response = await call_next(request)
        
        # Update CSP with nonce if present
        if "Content-Security-Policy" in response.headers:
            csp = response.headers["Content-Security-Policy"]
            # Add nonce to script-src and style-src
            csp = csp.replace("script-src", f"script-src 'nonce-{nonce}'")
            csp = csp.replace("style-src", f"style-src 'nonce-{nonce}'")
            response.headers["Content-Security-Policy"] = csp
        
        return response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Add request ID for tracking"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or get request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = secrets.token_urlsafe(16)
        
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


def setup_security_middleware(app):
    """Setup all security middleware"""
    
    # HTTPS redirect in production
    if settings.ssl_redirect and settings.environment == "production":
        app.add_middleware(HTTPSRedirectMiddleware)
    
    # Trusted host validation
    if settings.environment == "production":
        allowed_hosts = [
            "inventorysync.com",
            "*.inventorysync.com",
            "api.inventorysync.com"
        ]
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Request ID tracking
    app.add_middleware(RequestIdMiddleware)
    
    # Nonce for CSP
    if settings.environment == "production":
        app.add_middleware(NonceMiddleware)
