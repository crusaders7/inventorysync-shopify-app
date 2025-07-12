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
    
    def __init__(self, webhook_secret: str):
        self.webhook_secret = webhook_secret
    
    async def __call__(self, request: Request, call_next):
        # Only verify webhook endpoints
        if request.url.path.startswith("/api/webhooks/"):
            # Get the raw body
            body = await request.body()
            
            # Get the HMAC header
            hmac_header = request.headers.get("X-Shopify-Hmac-Sha256")
            
            if not hmac_header:
                logger.warning(f"Missing HMAC header for webhook: {request.url.path}")
                return JSONResponse(
                    status_code=401,
                    content={"error": "Unauthorized"}
                )
            
            # Verify the webhook
            if not self.verify_webhook(body, hmac_header):
                logger.warning(f"Invalid webhook signature for: {request.url.path}")
                return JSONResponse(
                    status_code=401,
                    content={"error": "Invalid signature"}
                )
            
            # Store body for later use
            request.state.webhook_body = body
        
        response = await call_next(request)
        return response
    
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
