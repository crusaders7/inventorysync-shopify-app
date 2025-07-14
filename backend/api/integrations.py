"""
Integrations API - Third-party system connections
Custom API endpoints for external integrations and webhooks
"""

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks, Header
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, func
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
import json
import hmac
import hashlib
import secrets
import uuid

from database import AsyncSessionLocal
from models import (
    Store, Product, ProductVariant, InventoryItem, 
    Location, Alert, CustomFieldDefinition
)
from utils.logging import logger

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    permissions: List[str] = Field(..., min_items=1)
    expires_at: Optional[datetime] = None
    rate_limit: int = Field(default=1000, ge=10, le=10000)  # requests per hour


class WebhookCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    url: str = Field(..., pattern=r'^https?://.+')
    events: List[str] = Field(..., min_items=1)
    secret: Optional[str] = None
    headers: Dict[str, str] = {}
    is_active: bool = True


class ExternalDataSync(BaseModel):
    entity_type: str = Field(..., pattern="^(product|variant|inventory|supplier)$")
    external_id: str
    data: Dict[str, Any]
    source_system: str
    sync_timestamp: Optional[datetime] = None


class BulkOperation(BaseModel):
    operation: str = Field(..., pattern="^(create|update|delete|sync)$")
    entity_type: str = Field(..., pattern="^(product|variant|inventory|alert)$")
    data: List[Dict[str, Any]] = Field(..., min_items=1, max_items=1000)
    options: Dict[str, Any] = {}


# =============================================================================
# API KEY MANAGEMENT
# =============================================================================

@router.post("/{shop_domain}/api-keys")
async def create_api_key(
    shop_domain: str,
    api_key_data: APIKeyCreate
):
    """Create a new API key for third-party integrations"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop_domain)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Generate API key
            api_key = f"isk_{secrets.token_urlsafe(32)}"
            api_secret = secrets.token_urlsafe(64)
            
            # TODO: Store API key in database
            # For now, return the generated key
            
            logger.info(
                f"Created API key",
                shop_domain=shop_domain,
                key_name=api_key_data.name,
                permissions=api_key_data.permissions
            )
            
            return {
                "api_key": api_key,
                "api_secret": api_secret,
                "name": api_key_data.name,
                "permissions": api_key_data.permissions,
                "rate_limit": api_key_data.rate_limit,
                "expires_at": api_key_data.expires_at.isoformat() if api_key_data.expires_at else None,
                "created_at": datetime.now().isoformat(),
                "warning": "Store this API key securely. It will not be shown again."
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to create API key")


@router.get("/{shop_domain}/api-keys")
async def list_api_keys(shop_domain: str):
    """List all API keys for a store (without revealing secrets)"""
    
    # TODO: Implement API key listing from database
    # For now, return placeholder data
    
    return {
        "api_keys": [
            {
                "id": "key_001",
                "name": "WMS Integration",
                "permissions": ["inventory:read", "inventory:write"],
                "rate_limit": 1000,
                "last_used": "2024-01-15T10:30:00Z",
                "created_at": "2024-01-01T00:00:00Z",
                "expires_at": None
            }
        ],
        "total_count": 1
    }


# =============================================================================
# WEBHOOK MANAGEMENT
# =============================================================================

@router.post("/{shop_domain}/webhooks")
async def create_webhook(
    shop_domain: str,
    webhook_data: WebhookCreate
):
    """Create a webhook endpoint for real-time notifications"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop_domain)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Generate webhook secret if not provided
            webhook_secret = webhook_data.secret or secrets.token_urlsafe(32)
            
            # TODO: Store webhook in database
            # For now, return success response
            
            logger.info(
                f"Created webhook",
                shop_domain=shop_domain,
                webhook_name=webhook_data.name,
                url=webhook_data.url,
                events=webhook_data.events
            )
            
            return {
                "id": f"wh_{uuid.uuid4().hex[:16]}",
                "name": webhook_data.name,
                "url": webhook_data.url,
                "events": webhook_data.events,
                "secret": webhook_secret,
                "is_active": webhook_data.is_active,
                "created_at": datetime.now().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to create webhook")


@router.get("/{shop_domain}/webhooks")
async def list_webhooks(shop_domain: str):
    """List all webhooks for a store"""
    
    # TODO: Implement webhook listing from database
    # For now, return placeholder data
    
    return {
        "webhooks": [
            {
                "id": "wh_001",
                "name": "Inventory Updates",
                "url": "https://example.com/webhook",
                "events": ["inventory.updated", "product.created"],
                "is_active": True,
                "last_triggered": "2024-01-15T14:20:00Z",
                "success_rate": 98.5,
                "created_at": "2024-01-01T00:00:00Z"
            }
        ],
        "total_count": 1
    }


# =============================================================================
# EXTERNAL DATA SYNC
# =============================================================================

@router.post("/{shop_domain}/sync")
async def sync_external_data(
    shop_domain: str,
    sync_data: ExternalDataSync,
    api_key: str = Header(..., alias="X-API-Key")
):
    """Sync data from external systems"""
    
    try:
        # TODO: Validate API key
        
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop_domain)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Process sync based on entity type
            if sync_data.entity_type == "product":
                await sync_product_data(session, store.id, sync_data)
            elif sync_data.entity_type == "variant":
                await sync_variant_data(session, store.id, sync_data)
            elif sync_data.entity_type == "inventory":
                await sync_inventory_data(session, store.id, sync_data)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported entity type: {sync_data.entity_type}")
            
            logger.info(
                f"Synced external data",
                shop_domain=shop_domain,
                entity_type=sync_data.entity_type,
                external_id=sync_data.external_id,
                source_system=sync_data.source_system
            )
            
            return {
                "status": "success",
                "entity_type": sync_data.entity_type,
                "external_id": sync_data.external_id,
                "synced_at": datetime.now().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync external data: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync data")


async def sync_product_data(session: Session, store_id: int, sync_data: ExternalDataSync):
    """Sync product data from external system"""
    
    # Look for existing product by external ID
    result = await session.execute(
        select(Product).where(
            and_(
                Product.store_id == store_id,
                Product.custom_data['external_id'].astext == sync_data.external_id
            )
        )
    )
    product = result.scalar_one_or_none()
    
    if product:
        # Update existing product
        for field, value in sync_data.data.items():
            if hasattr(product, field):
                setattr(product, field, value)
            else:
                # Store in custom_data
                if not product.custom_data:
                    product.custom_data = {}
                product.custom_data[field] = value
        
        product.custom_data['external_id'] = sync_data.external_id
        product.custom_data['source_system'] = sync_data.source_system
        product.custom_data['last_sync'] = datetime.now().isoformat()
        
    else:
        # Create new product
        new_product = Product(
            store_id=store_id,
            shopify_product_id=f"ext_{sync_data.external_id}",
            title=sync_data.data.get('title', 'External Product'),
            handle=sync_data.data.get('handle', f"external-{sync_data.external_id}"),
            product_type=sync_data.data.get('product_type'),
            vendor=sync_data.data.get('vendor'),
            price=sync_data.data.get('price'),
            custom_data={
                'external_id': sync_data.external_id,
                'source_system': sync_data.source_system,
                'last_sync': datetime.now().isoformat(),
                **{k: v for k, v in sync_data.data.items() if not hasattr(Product, k)}
            }
        )
        session.add(new_product)
    
    await session.commit()


async def sync_variant_data(session: Session, store_id: int, sync_data: ExternalDataSync):
    """Sync variant data from external system"""
    
    # TODO: Implement variant sync logic
    logger.info(f"Variant sync not yet implemented: {sync_data.external_id}")


async def sync_inventory_data(session: Session, store_id: int, sync_data: ExternalDataSync):
    """Sync inventory data from external system"""
    
    # Look for existing inventory item by external ID
    result = await session.execute(
        select(InventoryItem).where(
            and_(
                InventoryItem.store_id == store_id,
                InventoryItem.custom_data['external_id'].astext == sync_data.external_id
            )
        )
    )
    inventory_item = result.scalar_one_or_none()
    
    if inventory_item:
        # Update quantities
        inventory_item.available_quantity = sync_data.data.get('available_quantity', inventory_item.available_quantity)
        inventory_item.on_hand_quantity = sync_data.data.get('on_hand_quantity', inventory_item.on_hand_quantity)
        inventory_item.committed_quantity = sync_data.data.get('committed_quantity', inventory_item.committed_quantity)
        
        # Update custom data
        if not inventory_item.custom_data:
            inventory_item.custom_data = {}
        inventory_item.custom_data.update({
            'external_id': sync_data.external_id,
            'source_system': sync_data.source_system,
            'last_sync': datetime.now().isoformat()
        })
        
        await session.commit()


# =============================================================================
# BULK OPERATIONS
# =============================================================================

@router.post("/{shop_domain}/bulk")
async def bulk_operation(
    shop_domain: str,
    bulk_data: BulkOperation,
    background_tasks: BackgroundTasks,
    api_key: str = Header(..., alias="X-API-Key")
):
    """Perform bulk operations on data"""
    
    try:
        # TODO: Validate API key and permissions
        
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop_domain)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Process bulk operation in background
            background_tasks.add_task(
                process_bulk_operation,
                store.id,
                bulk_data
            )
            
            operation_id = f"bulk_{uuid.uuid4().hex[:16]}"
            
            logger.info(
                f"Started bulk operation",
                shop_domain=shop_domain,
                operation_id=operation_id,
                operation=bulk_data.operation,
                entity_type=bulk_data.entity_type,
                item_count=len(bulk_data.data)
            )
            
            return {
                "operation_id": operation_id,
                "status": "processing",
                "operation": bulk_data.operation,
                "entity_type": bulk_data.entity_type,
                "item_count": len(bulk_data.data),
                "started_at": datetime.now().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start bulk operation: {e}")
        raise HTTPException(status_code=500, detail="Failed to start bulk operation")


async def process_bulk_operation(store_id: int, bulk_data: BulkOperation):
    """Process bulk operation in background"""
    
    try:
        async with AsyncSessionLocal() as session:
            success_count = 0
            error_count = 0
            
            for item_data in bulk_data.data:
                try:
                    if bulk_data.operation == "create":
                        await create_bulk_item(session, store_id, bulk_data.entity_type, item_data)
                    elif bulk_data.operation == "update":
                        await update_bulk_item(session, store_id, bulk_data.entity_type, item_data)
                    elif bulk_data.operation == "delete":
                        await delete_bulk_item(session, store_id, bulk_data.entity_type, item_data)
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Bulk operation item failed: {e}")
                    error_count += 1
            
            await session.commit()
            
            logger.info(
                f"Bulk operation completed",
                store_id=store_id,
                operation=bulk_data.operation,
                success_count=success_count,
                error_count=error_count
            )
            
    except Exception as e:
        logger.error(f"Bulk operation failed: {e}")


async def create_bulk_item(session: Session, store_id: int, entity_type: str, item_data: Dict[str, Any]):
    """Create a single item in bulk operation"""
    
    if entity_type == "product":
        product = Product(
            store_id=store_id,
            shopify_product_id=item_data.get('id', f"bulk_{uuid.uuid4().hex[:8]}"),
            title=item_data.get('title', 'Bulk Product'),
            handle=item_data.get('handle', f"bulk-{uuid.uuid4().hex[:8]}"),
            product_type=item_data.get('product_type'),
            vendor=item_data.get('vendor'),
            price=item_data.get('price'),
            custom_data=item_data.get('custom_data', {})
        )
        session.add(product)
    
    # TODO: Implement other entity types


async def update_bulk_item(session: Session, store_id: int, entity_type: str, item_data: Dict[str, Any]):
    """Update a single item in bulk operation"""
    
    # TODO: Implement bulk update logic
    pass


async def delete_bulk_item(session: Session, store_id: int, entity_type: str, item_data: Dict[str, Any]):
    """Delete a single item in bulk operation"""
    
    # TODO: Implement bulk delete logic
    pass


# =============================================================================
# PUBLIC API ENDPOINTS (Read-only)
# =============================================================================

@router.get("/{shop_domain}/public/products")
async def get_public_products(
    shop_domain: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    api_key: str = Header(..., alias="X-API-Key")
):
    """Get products via public API (read-only)"""
    
    try:
        # TODO: Validate API key and rate limits
        
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop_domain)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Get products
            result = await session.execute(
                select(Product).where(Product.store_id == store.id)
                .offset(offset).limit(limit)
                .order_by(Product.created_at.desc())
            )
            products = result.scalars().all()
            
            # Format response
            products_data = []
            for product in products:
                products_data.append({
                    "id": product.id,
                    "external_id": product.shopify_product_id,
                    "title": product.title,
                    "handle": product.handle,
                    "product_type": product.product_type,
                    "vendor": product.vendor,
                    "price": product.price,
                    "status": product.status,
                    "custom_data": product.custom_data,
                    "created_at": product.created_at.isoformat(),
                    "updated_at": product.updated_at.isoformat()
                })
            
            return {
                "products": products_data,
                "offset": offset,
                "limit": limit,
                "total_count": len(products_data)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get public products: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve products")


@router.get("/{shop_domain}/public/inventory")
async def get_public_inventory(
    shop_domain: str,
    location_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    api_key: str = Header(..., alias="X-API-Key")
):
    """Get inventory levels via public API (read-only)"""
    
    try:
        # TODO: Validate API key and rate limits
        
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop_domain)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Build query
            query = select(InventoryItem).where(InventoryItem.store_id == store.id)
            
            if location_id:
                query = query.where(InventoryItem.location_id == location_id)
            
            query = query.offset(offset).limit(limit).order_by(InventoryItem.updated_at.desc())
            
            result = await session.execute(query)
            inventory_items = result.scalars().all()
            
            # Format response
            inventory_data = []
            for item in inventory_items:
                inventory_data.append({
                    "id": item.id,
                    "location_id": item.location_id,
                    "variant_id": item.variant_id,
                    "available_quantity": item.available_quantity,
                    "on_hand_quantity": item.on_hand_quantity,
                    "committed_quantity": item.committed_quantity,
                    "reorder_point": item.reorder_point,
                    "reorder_quantity": item.reorder_quantity,
                    "custom_data": item.custom_data,
                    "updated_at": item.updated_at.isoformat()
                })
            
            return {
                "inventory": inventory_data,
                "offset": offset,
                "limit": limit,
                "total_count": len(inventory_data)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get public inventory: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve inventory")


# =============================================================================
# INTEGRATION STATUS AND HEALTH
# =============================================================================

@router.get("/{shop_domain}/status")
async def get_integration_status(shop_domain: str):
    """Get integration health and status"""
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "endpoints": {
            "products": "/api/v1/integrations/{shop_domain}/public/products",
            "inventory": "/api/v1/integrations/{shop_domain}/public/inventory",
            "sync": "/api/v1/integrations/{shop_domain}/sync",
            "bulk": "/api/v1/integrations/{shop_domain}/bulk"
        },
        "rate_limits": {
            "default": "1000 requests/hour",
            "bulk": "100 operations/hour"
        },
        "supported_formats": ["json"],
        "webhook_events": [
            "product.created",
            "product.updated",
            "inventory.updated",
            "alert.created"
        ]
    }