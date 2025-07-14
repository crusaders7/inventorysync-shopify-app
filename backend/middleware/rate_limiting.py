"""
Rate limiting middleware to prevent API abuse
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
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


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute)
        
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/redoc"]:
            return await call_next(request)
            
        # Get client identifier (IP or shop domain)
        client_ip = request.client.host if request.client else "unknown"
        shop_domain = request.headers.get("X-Shopify-Shop-Domain", client_ip)
        identifier = f"{shop_domain}:{request.url.path}"
        
        # Check rate limit
        if not self.limiter.is_allowed(identifier):
            reset_time = self.limiter.get_reset_time(identifier)
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please retry after {reset_time} seconds",
                    "retry_after": reset_time
                },
                headers={
                    "X-RateLimit-Limit": str(self.limiter.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + reset_time),
                    "Retry-After": str(reset_time)
                }
            )
            
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self.limiter.requests_per_minute - len(self.limiter.requests[identifier])
        response.headers["X-RateLimit-Limit"] = str(self.limiter.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
        
        return response


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
