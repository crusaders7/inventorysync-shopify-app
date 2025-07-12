"""
API Versioning and Cache Management Utility
Handles environment-based API versioning and cache invalidation
"""

import os
import hashlib
import time
from datetime import datetime
from typing import Dict, Optional, Tuple
from functools import lru_cache
from config import settings
from utils.logging import logger


class APIVersionManager:
    """Manages API versions and cache invalidation strategies"""
    
    # Version history mapping
    VERSION_HISTORY = {
        "v1": {
            "release_date": "2024-01-01",
            "deprecated": False,
            "sunset_date": None,
            "features": ["basic_inventory", "alerts", "reports"]
        },
        "v2": {
            "release_date": "2024-06-01", 
            "deprecated": False,
            "sunset_date": None,
            "features": ["custom_fields", "workflows", "advanced_analytics"]
        }
    }
    
    def __init__(self):
        self.current_version = self._get_current_version()
        self.deployment_hash = self._generate_deployment_hash()
        self.cache_version = self._get_cache_version()
        
    def _get_current_version(self) -> str:
        """Get current API version based on environment"""
        # Check environment variable first
        env_version = os.getenv("API_VERSION")
        if env_version and env_version in self.VERSION_HISTORY:
            return env_version
            
        # Default version based on environment
        if settings.environment == "production":
            return "v1"  # Stable version for production
        elif settings.environment == "staging":
            return "v2"  # Latest version for staging
        else:
            return "v2"  # Development uses latest
            
    def _generate_deployment_hash(self) -> str:
        """Generate unique hash for current deployment"""
        # Combine various factors to create deployment identifier
        factors = [
            settings.app_version,
            settings.environment,
            str(os.getenv("DEPLOYMENT_ID", "")),
            str(os.getenv("BUILD_NUMBER", "")),
            str(int(time.time() // 3600))  # Changes every hour
        ]
        
        combined = "-".join(factors)
        return hashlib.md5(combined.encode()).hexdigest()[:8]
        
    def _get_cache_version(self) -> str:
        """Get cache version for cache-busting"""
        # In production, use deployment hash
        if settings.environment == "production":
            return self.deployment_hash
            
        # In development, use timestamp for frequent updates
        return str(int(time.time() // 60))  # Changes every minute
        
    def get_api_prefix(self, version: Optional[str] = None) -> str:
        """Get API prefix with version"""
        version = version or self.current_version
        return f"/api/{version}"
        
    def get_cache_headers(self) -> Dict[str, str]:
        """Get cache-busting headers"""
        return {
            "X-API-Version": self.current_version,
            "X-Cache-Version": self.cache_version,
            "X-Deployment-ID": self.deployment_hash,
            "Cache-Control": self._get_cache_control(),
            "ETag": self._generate_etag()
        }
        
    def _get_cache_control(self) -> str:
        """Get cache control header based on environment"""
        if settings.environment == "production":
            # Cache static resources for 1 hour, but revalidate
            return "public, max-age=3600, must-revalidate"
        else:
            # No caching in development
            return "no-cache, no-store, must-revalidate"
            
    def _generate_etag(self) -> str:
        """Generate ETag for response caching"""
        return f'W/"{self.current_version}-{self.cache_version}"'
        
    def validate_version(self, version: str) -> Tuple[bool, Optional[str]]:
        """Validate if API version is supported"""
        if version not in self.VERSION_HISTORY:
            return False, f"Unknown API version: {version}"
            
        version_info = self.VERSION_HISTORY[version]
        
        if version_info["deprecated"]:
            sunset_date = version_info.get("sunset_date")
            return True, f"Warning: API {version} is deprecated. Sunset date: {sunset_date}"
            
        return True, None
        
    def get_version_info(self, version: Optional[str] = None) -> Dict:
        """Get detailed version information"""
        version = version or self.current_version
        
        if version not in self.VERSION_HISTORY:
            return {"error": "Version not found"}
            
        info = self.VERSION_HISTORY[version].copy()
        info["version"] = version
        info["current"] = version == self.current_version
        info["cache_version"] = self.cache_version
        info["deployment_id"] = self.deployment_hash
        
        return info
        
    def should_invalidate_cache(self, last_deployment_hash: Optional[str]) -> bool:
        """Check if cache should be invalidated based on deployment"""
        if not last_deployment_hash:
            return True
            
        return last_deployment_hash != self.deployment_hash
        
    def get_versioned_endpoint(self, endpoint: str, version: Optional[str] = None) -> str:
        """Get fully qualified versioned endpoint"""
        version = version or self.current_version
        prefix = self.get_api_prefix(version)
        
        # Ensure endpoint starts with /
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
            
        return f"{prefix}{endpoint}"
        
    def log_version_usage(self, version: str, endpoint: str, method: str):
        """Log API version usage for monitoring"""
        logger.info(
            f"API Version Usage - Version: {version}, Endpoint: {endpoint}, "
            f"Method: {method}, Environment: {settings.environment}, "
            f"Deployment: {self.deployment_hash}"
        )


# Global instance
version_manager = APIVersionManager()


def get_version_manager() -> APIVersionManager:
    """Get the global version manager instance"""
    return version_manager


# Cache invalidation decorator
def cache_versioned(max_age: int = 300):
    """Decorator to add versioned caching to endpoints"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Add cache headers to response
            response = await func(*args, **kwargs)
            
            # If response is a dict, we need to wrap it
            if isinstance(response, dict):
                from fastapi.responses import JSONResponse
                headers = version_manager.get_cache_headers()
                headers["Cache-Control"] = f"public, max-age={max_age}, must-revalidate"
                
                return JSONResponse(
                    content=response,
                    headers=headers
                )
                
            return response
            
        return wrapper
    return decorator


# Environment-based configuration loader
@lru_cache(maxsize=1)
def get_api_configuration() -> Dict:
    """Get environment-specific API configuration"""
    base_config = {
        "version": version_manager.current_version,
        "deployment_id": version_manager.deployment_hash,
        "cache_version": version_manager.cache_version,
        "environment": settings.environment,
        "features": version_manager.VERSION_HISTORY.get(
            version_manager.current_version, {}
        ).get("features", []),
        "rate_limits": {
            "development": {"per_minute": 600, "burst": 100},
            "staging": {"per_minute": 300, "burst": 50},
            "production": {"per_minute": 100, "burst": 20}
        }.get(settings.environment, {"per_minute": 60, "burst": 10}),
        "cache_ttl": {
            "development": 0,  # No caching
            "staging": 300,    # 5 minutes
            "production": 3600 # 1 hour
        }.get(settings.environment, 60)
    }
    
    return base_config
