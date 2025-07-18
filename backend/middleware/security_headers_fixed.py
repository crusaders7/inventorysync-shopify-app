"""
Security headers middleware for enhanced security
"""
from typing import Callable
from fastapi import Request, Response

class SecurityHeadersMiddleware:
    """Add security headers to all responses"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                
                # Add security headers for Shopify embedded app
                headers[b"x-content-type-options"] = b"nosniff"
                # X-Frame-Options removed to allow Shopify embedding
                # headers[b"x-frame-options"] = b"DENY"
                headers[b"x-xss-protection"] = b"1; mode=block"
                headers[b"referrer-policy"] = b"strict-origin-when-cross-origin"
                
                # Content Security Policy - Updated for Shopify embedding and analytics
                csp = (
                    "default-src *; "
                    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.shopify.com https://*.shopify.com https://*.shopifysvc.com; "
                    "style-src 'self' 'unsafe-inline' https://cdn.shopify.com; "
                    "img-src 'self' data: https: blob:; "
                    "font-src 'self' data: https://cdn.shopify.com; "
                    "connect-src 'self' https://*.shopify.com https://*.shopifysvc.com wss: https: "
                    "https://monorail-edge.shopifysvc.com https://error-analytics-sessions-production.shopifysvc.com "
                    "https://otlp-http-production.shopifysvc.com; "
                    "frame-ancestors *; "
                    "base-uri 'self'; "
                    "form-action 'self'"
                )
                headers[b"content-security-policy"] = csp.encode()
                
                # HSTS for HTTPS
                if scope.get("scheme") == "https":
                    headers[b"strict-transport-security"] = b"max-age=31536000; includeSubDomains"
                
                # Permissions Policy
                permissions = "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"
                headers[b"permissions-policy"] = permissions.encode()
                
                # Update message with new headers
                message["headers"] = [(k, v) for k, v in headers.items()]
                
            await send(message)
            
        await self.app(scope, receive, send_wrapper)
