"""
Multi-Location Management API
Handles location-based inventory operations
"""

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_

from database import AsyncSessionLocal
from models import Store, Location
from multi_location_sync import multi_location_sync
from utils.logging import logger

router = APIRouter(prefix="/api/v1/locations", tags=["locations"])


@router.get("/")
async def list_locations(
    shop: str = Query(..., description="Shop domain"),
    include_inactive: bool = Query(False, description="Include inactive locations")
):
    """List all locations for a store"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Get locations
            query = select(Location).where(Location.store_id == store.id)
            if not include_inactive:
                query = query.where(Location.is_active == True)
            
            result = await session.execute(query)
            locations = result.scalars().all()
            
            return {
                "locations": [
                    {
                        "id": loc.id,
                        "shopify_location_id": loc.shopify_location_id,
                        "name": loc.name,
                        "address": loc.address,
                        "type": loc.location_type,
                        "is_active": loc.is_active,
                        "is_primary": loc.is_primary,
                        "inventory_tracked": loc.inventory_tracked
                    }
                    for loc in locations
                ],
                "total": len(locations)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list locations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve locations")


@router.post("/sync")
async def sync_locations(
    shop: str = Query(..., description="Shop domain"),
    background_tasks: BackgroundTasks = None
):
    """Sync inventory across all locations"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Check if multi-location is enabled
            if not store.plan_features.get("multi_location", False):
                raise HTTPException(
                    status_code=403,
                    detail="Multi-location sync not available in your current plan"
                )
            
            # Start sync
            sync_results = await multi_location_sync.sync_all_locations(store.id)
            
            logger.info(
                f"Location sync initiated",
                shop=shop,
                results=sync_results
            )
            
            return sync_results
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Location sync failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Sync failed")


@router.get("/transfers/suggestions")
async def get_transfer_suggestions(
    shop: str = Query(..., description="Shop domain"),
    limit: int = Query(10, ge=1, le=50, description="Maximum suggestions")
):
    """Get intelligent transfer suggestions between locations"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Check features
            if not store.plan_features.get("multi_location", False):
                raise HTTPException(
                    status_code=403,
                    detail="Multi-location features not available in your current plan"
                )
            
            # Get locations
            result = await session.execute(
                select(Location).where(
                    and_(
                        Location.store_id == store.id,
                        Location.is_active == True
                    )
                )
            )
            locations = result.scalars().all()
            
            if len(locations) < 2:
                return {
                    "suggestions": [],
                    "message": "At least 2 active locations required for transfers"
                }
            
            # Analyze and get suggestions
            imbalances = await multi_location_sync._analyze_inventory_distribution(
                session, store.id, locations
            )
            
            suggestions = await multi_location_sync._generate_transfer_suggestions(
                session, store.id, locations, imbalances
            )
            
            return {
                "suggestions": suggestions[:limit],
                "total_imbalances": len(imbalances),
                "generated_at": datetime.utcnow().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get transfer suggestions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate suggestions")


@router.post("/transfers/create")
async def create_transfer(
    transfer_data: dict,
    shop: str = Query(..., description="Shop domain")
):
    """Create a new inventory transfer between locations"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Create transfer
            transfer_result = await multi_location_sync.create_transfer_order(
                store.id, transfer_data
            )
            
            logger.info(
                f"Transfer created",
                shop=shop,
                transfer_id=transfer_result["transfer_id"]
            )
            
            return transfer_result
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create transfer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create transfer")


@router.get("/{location_id}/performance")
async def get_location_performance(
    location_id: int,
    shop: str = Query(..., description="Shop domain"),
    days: int = Query(30, ge=1, le=365, description="Days to analyze")
):
    """Get performance metrics for a specific location"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Get performance data
            performance = await multi_location_sync.get_location_performance(
                store.id, location_id, days
            )
            
            return performance
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get location performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get performance data")


@router.get("/heatmap")
async def get_inventory_heatmap(
    shop: str = Query(..., description="Shop domain")
):
    """Get inventory distribution heatmap across locations"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store and locations
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # This would generate a heatmap visualization data
            # For now, return sample structure
            heatmap_data = {
                "locations": [
                    {
                        "id": 1,
                        "name": "Main Warehouse",
                        "inventory_value": 125000,
                        "product_count": 450,
                        "utilization": 0.78
                    },
                    {
                        "id": 2,
                        "name": "Downtown Store",
                        "inventory_value": 45000,
                        "product_count": 180,
                        "utilization": 0.65
                    }
                ],
                "metrics": {
                    "total_value": 170000,
                    "average_utilization": 0.71,
                    "imbalance_score": 0.23
                }
            }
            
            return heatmap_data
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate heatmap: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate heatmap")