"""
Shopify API Client
Handles all Shopify API interactions for InventorySync
"""

import os
import hashlib
import hmac
import base64
import json
from typing import Optional, Dict, Any, List
from urllib.parse import urlencode, parse_qs
import httpx
from fastapi import HTTPException
import logging
from datetime import datetime

# Import our utilities
from utils.logging import logger
from utils.validation import ShopDomainValidator
from utils.cache import cache, cached
from config import settings

logger = logging.getLogger(__name__)


class ShopifyClient:
    """Shopify API client for inventory management"""
    
    def __init__(self, shop_domain: str, access_token: str):
        # Validate and normalize shop domain
        self.shop_domain = ShopDomainValidator.validate(shop_domain)
        self.access_token = access_token
        self.shop_name = self.shop_domain.replace('.myshopify.com', '')
        self.base_url = f"https://{self.shop_name}.myshopify.com"
        self.api_version = "2024-01"
        
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        timeout: int = 30
    ) -> Dict[Any, Any]:
        """Make authenticated request to Shopify API with comprehensive logging"""
        
        url = f"{self.base_url}/admin/api/{self.api_version}/{endpoint}"
        
        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"InventorySync/{getattr(settings, 'app_version', '1.0.0')}"
        }
        
        start_time = datetime.now()
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=headers, json=data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Calculate response time
                response_time = (datetime.now() - start_time).total_seconds()
                
                # Log successful API call
                logger.shopify_api_call(
                    endpoint=endpoint,
                    method=method.upper(),
                    status_code=response.status_code,
                    response_time=response_time,
                    shop=self.shop_domain
                )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Log API error with details
            logger.error(
                f"Shopify API error: {e.response.status_code}",
                shop_domain=self.shop_domain,
                endpoint=endpoint,
                method=method.upper(),
                status_code=e.response.status_code,
                response_time=response_time,
                error_details=e.response.text[:500] if e.response.text else None
            )
            
            # Handle specific error cases
            if e.response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Shopify authentication failed - access token may be invalid"
                )
            elif e.response.status_code == 429:
                raise HTTPException(
                    status_code=429,
                    detail="Shopify API rate limit exceeded - please try again later"
                )
            elif e.response.status_code == 403:
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient permissions for this Shopify operation"
                )
            else:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Shopify API error: {e.response.status_code}"
                )
                
        except httpx.TimeoutException:
            logger.error(
                f"Shopify API timeout",
                shop_domain=self.shop_domain,
                endpoint=endpoint,
                method=method.upper(),
                timeout=timeout
            )
            raise HTTPException(
                status_code=504,
                detail="Shopify API request timed out"
            )
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            logger.error(
                f"Shopify API request failed: {str(e)}",
                shop_domain=self.shop_domain,
                endpoint=endpoint,
                method=method.upper(),
                response_time=response_time,
                exc_info=e
            )
            raise HTTPException(
                status_code=500,
                detail="Shopify API request failed"
            )
    
    # Product Management
    @cached(ttl=300, key_prefix="shopify:products")
    async def get_products(self, limit: int = 50, page_info: Optional[str] = None) -> Dict:
        """Get products from Shopify store with caching (5 min TTL)"""
        params = {"limit": limit}
        if page_info:
            params["page_info"] = page_info
            
        return await self._make_request("GET", "products.json", params=params)
    
    @cached(ttl=300, key_prefix="shopify:product")
    async def get_product(self, product_id: str) -> Dict:
        """Get single product by ID with caching (5 min TTL)"""
        return await self._make_request("GET", f"products/{product_id}.json")
    
    @cached(ttl=300, key_prefix="shopify:variants")
    async def get_product_variants(self, product_id: str) -> Dict:
        """Get variants for a specific product with caching (5 min TTL)"""
        return await self._make_request("GET", f"products/{product_id}/variants.json")
    
    # Inventory Management
    @cached(ttl=60, key_prefix="shopify:inventory_levels")
    async def get_inventory_levels(self, location_id: Optional[str] = None) -> Dict:
        """Get inventory levels with caching (1 min TTL for fresher data)"""
        params = {}
        if location_id:
            params["location_ids"] = location_id
            
        return await self._make_request("GET", "inventory_levels.json", params=params)
    
    @cached(ttl=300, key_prefix="shopify:inventory_item")
    async def get_inventory_item(self, inventory_item_id: str) -> Dict:
        """Get inventory item details with caching (5 min TTL)"""
        return await self._make_request("GET", f"inventory_items/{inventory_item_id}.json")
    
    async def update_inventory_level(
        self, 
        location_id: str, 
        inventory_item_id: str, 
        available: int
    ) -> Dict:
        """Update inventory level for a specific location and item"""
        data = {
            "location_id": location_id,
            "inventory_item_id": inventory_item_id,
            "available": available
        }
        result = await self._make_request("POST", "inventory_levels/adjust.json", data=data)
        
        # Invalidate related caches after update
        await cache.delete_pattern(f"shopify:inventory_levels:*")
        await cache.delete_pattern(f"shopify:inventory_item:{inventory_item_id}*")
        
        return result
    
    # Location Management
    @cached(ttl=3600, key_prefix="shopify:locations")
    async def get_locations(self) -> Dict:
        """Get all store locations with caching (1 hour TTL)"""
        return await self._make_request("GET", "locations.json")
    
    @cached(ttl=3600, key_prefix="shopify:location")
    async def get_location(self, location_id: str) -> Dict:
        """Get specific location details with caching (1 hour TTL)"""
        return await self._make_request("GET", f"locations/{location_id}.json")
    
    # Shop Information
    async def get_shop_info(self) -> Dict:
        """Get shop information"""
        return await self._make_request("GET", "shop.json")
    
    # Webhooks
    async def create_webhook(self, topic: str, address: str) -> Dict:
        """Create a webhook subscription"""
        data = {
            "webhook": {
                "topic": topic,
                "address": address,
                "format": "json"
            }
        }
        return await self._make_request("POST", "webhooks.json", data=data)
    
    async def get_webhooks(self) -> Dict:
        """Get all webhooks"""
        return await self._make_request("GET", "webhooks.json")


class ShopifyAuth:
    """Handle Shopify OAuth authentication"""
    
    def __init__(self):
        self.api_key = settings.shopify_api_key
        self.api_secret = settings.shopify_api_secret
        self.webhook_secret = getattr(settings, 'shopify_webhook_secret', None)
        
        # Default scopes for inventory management
        self.scopes = [
            "read_products",
            "write_products", 
            "read_inventory",
            "write_inventory",
            "read_locations",
            "read_orders",
            "read_analytics"
        ]
        
        self.redirect_uri = f"{getattr(settings, 'app_url', 'http://localhost:8000')}/api/v1/auth/callback"
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Shopify API credentials not configured in settings")
    
    def get_auth_url(self, shop_domain: str, state: str) -> str:
        """Generate Shopify OAuth authorization URL with enhanced security"""
        # Validate and normalize shop domain
        shop_domain = ShopDomainValidator.validate(shop_domain)
        shop_name = shop_domain.replace('.myshopify.com', '')
        
        params = {
            "client_id": self.api_key,
            "scope": ",".join(self.scopes),
            "redirect_uri": self.redirect_uri,
            "state": state,
            "grant_options[]": "per-user"  # Enhanced security
        }
        
        auth_url = f"https://{shop_name}.myshopify.com/admin/oauth/authorize"
        return f"{auth_url}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, shop_domain: str, code: str) -> str:
        """Exchange authorization code for access token"""
        shop_domain = shop_domain.replace('.myshopify.com', '')
        
        data = {
            "client_id": self.api_key,
            "client_secret": self.api_secret,
            "code": code
        }
        
        url = f"https://{shop_domain}.myshopify.com/admin/oauth/access_token"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            response.raise_for_status()
            
            result = response.json()
            return result["access_token"]
    
    def verify_webhook(self, data: bytes, hmac_header: str) -> bool:
        """Verify webhook authenticity"""
        calculated_hmac = base64.b64encode(
            hmac.new(
                self.api_secret.encode('utf-8'),
                data,
                hashlib.sha256
            ).digest()
        ).decode()
        
        return hmac.compare_digest(calculated_hmac, hmac_header)
    
    def verify_request(self, query_params: Dict[str, str]) -> bool:
        """Verify request authenticity"""
        if 'hmac' not in query_params:
            return False
        
        hmac_to_verify = query_params.pop('hmac')
        
        # Sort parameters and create query string
        sorted_params = sorted(query_params.items())
        query_string = urlencode(sorted_params)
        
        calculated_hmac = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(calculated_hmac, hmac_to_verify)


# Utility functions
def get_shopify_client(shop_domain: str, access_token: str) -> ShopifyClient:
    """Factory function to create Shopify client"""
    return ShopifyClient(shop_domain, access_token)


async def sync_products_from_shopify(client: ShopifyClient) -> List[Dict]:
    """Sync all products from Shopify"""
    all_products = []
    page_info = None
    
    while True:
        response = await client.get_products(limit=50, page_info=page_info)
        products = response.get("products", [])
        all_products.extend(products)
        
        # Check for pagination
        link_header = response.get("link")
        if not link_header or "next" not in link_header:
            break
            
        # Extract next page info (simplified)
        page_info = "next_page_token"  # This would be parsed from Link header
    
    return all_products


async def sync_inventory_from_shopify(client: ShopifyClient) -> List[Dict]:
    """Sync inventory levels from Shopify"""
    locations = await client.get_locations()
    all_inventory = []
    
    for location in locations.get("locations", []):
        inventory = await client.get_inventory_levels(location["id"])
        all_inventory.extend(inventory.get("inventory_levels", []))
    
    return all_inventory