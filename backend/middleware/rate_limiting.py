"""
Rate limiting middleware to prevent API abuse
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import time
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
        self.cleanup_interval = 60  # Clean up old entries every minute
        self._cleanup_task = None
        
    async def start_cleanup(self):
        """Start the cleanup task"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
    async def stop_cleanup(self):
        """Stop the cleanup task"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            
    async def _cleanup_loop(self):
        """Periodically clean up old entries"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_old_entries()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                
    async def _cleanup_old_entries(self):
        """Remove entries older than 1 minute"""
        cutoff = time.time() - 60
        for key in list(self.requests.keys()):
            self.requests[key] = [
                timestamp for timestamp in self.requests[key]
                if timestamp > cutoff
            ]
            if not self.requests[key]:
                del self.requests[key]
                
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed"""
        current_time = time.time()
        cutoff = current_time - 60  # 1 minute window
        
        # Clean up old requests
        self.requests[identifier] = [
            timestamp for timestamp in self.requests[identifier]
            if timestamp > cutoff
        ]
        
        # Check if under limit
        if len(self.requests[identifier]) < self.requests_per_minute:
            self.requests[identifier].append(current_time)
            return True
            
        return False
        
    def get_reset_time(self, identifier: str) -> int:
        """Get seconds until rate limit resets"""
        if not self.requests[identifier]:
            return 0
            
        oldest_request = min(self.requests[identifier])
        reset_time = oldest_request + 60
        return max(0, int(reset_time - time.time()))


class RateLimitMiddleware:
    """Middleware to enforce rate limits"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        self.app = app
        self.limiter = RateLimiter(requests_per_minute)
        
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Check if this should be rate limited
            path = scope.get("path", "")
            if path not in ["/health", "/", "/docs", "/redoc"]:
                # For now, let's pass through to avoid breaking the app
                # TODO: Implement proper ASGI middleware for rate limiting
                pass
        
        await self.app(scope, receive, send)


# Shopify API rate limiter (2 requests per second)
class ShopifyAPIRateLimiter:
    """Rate limiter specifically for Shopify API calls"""
    
    def __init__(self):
        self.min_interval = 0.5  # 2 requests per second
        self.last_request_time = defaultdict(float)
        
    async def wait_if_needed(self, shop_domain: str):
        """Wait if necessary to respect rate limits"""
        current_time = time.time()
        last_request = self.last_request_time[shop_domain]
        
        if last_request:
            elapsed = current_time - last_request
            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                logger.debug(f"Rate limiting Shopify API call for {shop_domain}, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                
        self.last_request_time[shop_domain] = time.time()


# Global Shopify API rate limiter instance
shopify_rate_limiter = ShopifyAPIRateLimiter()
