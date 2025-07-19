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
                headers[b"x-xss-protection"] = b"1; mode=block"
                headers[b"referrer-policy"] = b"strict-origin-when-cross-origin"
                
                # Content Security Policy - Updated for Shopify embedding and analytics
                csp = (
                    "default-src * 'unsafe-inline' 'unsafe-eval'; "
                    "script-src * 'unsafe-inline' 'unsafe-eval'; "
                    "style-src * 'unsafe-inline'; "
                    "img-src * data: blob:; "
                    "font-src * data:; "
                    "connect-src *; "
                    "frame-ancestors * https://*.myshopify.com https://admin.shopify.com https://*.shopify.com;"
                )
                headers[b"content-security-policy"] = csp.encode()
                
                # Remove x-frame-options header to allow embedding
                if b"x-frame-options" in headers:
                    del headers[b"x-frame-options"]
                
                # Update message with new headers
                message["headers"] = [(k, v) for k, v in headers.items()]
                
            await send(message)
            
        await self.app(scope, receive, send_wrapper)
