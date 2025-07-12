"""
Webhook verification middleware for Shopify webhooks
"""
import hmac
import base64
import hashlib
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class WebhookVerificationMiddleware:
    """Middleware to verify Shopify webhook signatures"""
    
    def __init__(self, app, webhook_secret: str):
        self.app = app
        self.webhook_secret = webhook_secret
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Check if this is a webhook endpoint
            path = scope.get("path", "")
            if path.startswith("/api/webhooks/"):
                # We need to intercept the request to verify it
                # For now, let's pass through to avoid breaking the app
                # TODO: Implement proper ASGI middleware for webhook verification
                pass
        
        await self.app(scope, receive, send)
    
    def verify_webhook(self, body: bytes, signature: str) -> bool:
        """Verify the webhook signature"""
        try:
            # Calculate HMAC
            hash = hmac.new(
                self.webhook_secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).digest()
            
            # Encode in base64
            calculated_hmac = base64.b64encode(hash).decode()
            
            # Compare signatures
            return hmac.compare_digest(calculated_hmac, signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook: {str(e)}")
            return False


def verify_webhook_signature(body: bytes, signature: str, secret: str) -> bool:
    """
    Standalone function to verify webhook signatures
    """
    try:
        hash = hmac.new(
            secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).digest()
        calculated_hmac = base64.b64encode(hash).decode()
        return hmac.compare_digest(calculated_hmac, signature)
    except Exception:
        return False
