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
                
                # Remove existing security headers
                headers.pop(b"x-frame-options", None)
                headers.pop(b"content-security-policy", None)
                headers.pop(b"x-content-type-options", None)
                headers.pop(b"x-xss-protection", None)
                headers.pop(b"referrer-policy", None)
                
                # Add our security headers
                headers[b"access-control-allow-origin"] = b"*"
                headers[b"content-security-policy"] = b"default-src * 'unsafe-inline' 'unsafe-eval'; frame-ancestors * https://*.myshopify.com https://admin.shopify.com https://*.shopify.com;"
                
                # Update message with new headers
                message["headers"] = [(k, v) for k, v in headers.items()]
                
            await send(message)
            
        await self.app(scope, receive, send_wrapper)
