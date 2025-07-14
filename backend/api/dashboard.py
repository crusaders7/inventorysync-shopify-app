"""
Dashboard API Endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
import random
import logging

# Import validation utilities
from utils.validation import ShopDomainValidator, sanitize_string
from utils.logging import logger
from utils.exceptions import validation_error, internal_server_error

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_dashboard_stats(shop: str = Query(None)):
    """
    Get dashboard statistics
    """
    try:
        # Validate shop domain if provided
        if shop:
            shop = ShopDomainValidator.validate(shop)
            
            try:
                from shopify_sync import ShopifySync
                
                # Log Shopify API call attempt
                logger.info(f"Fetching stats from Shopify for shop: {shop}")
                
                async with ShopifySync(shop) as sync_service:
                    await sync_service.initialize()
                    stats = await sync_service.get_inventory_stats()
                    stats["lastSync"] = datetime.now().isoformat()
                    stats["syncStatus"] = "success"
                    
                    # Log successful stats retrieval
                    logger.info(f"Successfully retrieved stats from Shopify for shop: {shop}, total_products: {stats.get('totalProducts', 0)}")
                    
                    return stats
            except Exception as e:
                logger.error(f"Failed to get real stats for {shop}: {str(e)}", exc_info=e)
                # Continue to fallback data
        
        # Fallback to mock data
        logger.info("Using mock dashboard statistics")
        return {
            "totalProducts": 1247,
            "lowStockAlerts": 23,
            "totalValue": 125430,
            "activeLocations": 3,
            "lastSync": datetime.now().isoformat(),
            "syncStatus": "mock_data"
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {str(e)}", exc_info=e)
        raise

@router.get("/alerts")
async def get_recent_alerts():
    """
    Get recent inventory alerts
    """
    alerts = [
        {
            "id": "1",
            "type": "low_stock",
            "title": "Low Stock Alert",
            "product": "Blue T-Shirt (M)",
            "message": "Only 5 units left",
            "severity": "warning",
            "created_at": (datetime.now() - timedelta(hours=2)).isoformat()
        },
        {
            "id": "2",
            "type": "out_of_stock",
            "title": "Out of Stock",
            "product": "Red Sneakers (42)",
            "message": "Reorder required",
            "severity": "critical",
            "created_at": (datetime.now() - timedelta(hours=5)).isoformat()
        },
        {
            "id": "3",
            "type": "overstock",
            "title": "Overstock Alert",
            "product": "Green Hat",
            "message": "200% over target",
            "severity": "info",
            "created_at": (datetime.now() - timedelta(days=1)).isoformat()
        }
    ]
    
    return {
        "alerts": alerts,
        "total": len(alerts),
        "unread": 2
    }

@router.get("/trends")
async def get_inventory_trends(days: int = Query(7, ge=1, le=90)):
    """
    Get inventory trend data for charts
    """
    try:
        # Validate days parameter
        if days < 1 or days > 90:
            raise validation_error("Days must be between 1 and 90")
        
        # Generate mock trend data
        trends = []
        
        for i in range(days):
            date = datetime.now() - timedelta(days=days-i-1)
            trends.append({
                "date": date.strftime("%Y-%m-%d"),
                "total_products": 1200 + random.randint(-50, 50),
                "low_stock": 20 + random.randint(-5, 10),
                "total_value": 120000 + random.randint(-5000, 10000)
            })
        
        # Log trends request
        logger.info(f"Generated trend data for {days} days with {len(trends)} data points")
        
        return {
            "trends": trends,
            "period": f"{days} days",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get inventory trends: {str(e)}", exc_info=e)
        raise

@router.post("/sync")
async def trigger_inventory_sync(shop: str = Query(...)):
    """
    Trigger manual inventory sync from Shopify
    """
    try:
        # Validate shop domain
        shop = ShopDomainValidator.validate(shop)
        
        # Log sync start
        logger.info(f"Manual sync triggered for shop: {shop} [action=sync_start]")
        
        try:
            from shopify_sync import sync_shopify_store
            
            result = await sync_shopify_store(shop)
            
            # Log successful sync
            logger.info(f"Sync completed successfully for shop: {shop}, total_products: {result.get('total_products', 0)} [action=sync_complete]")
            
            return {
                "status": "completed",
                "message": f"Synced {result['total_products']} products successfully",
                "details": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except ImportError:
            # Shopify sync module not available - return mock response
            logger.warning(f"Shopify sync module not available, returning mock response for shop: {shop}")
            
            return {
                "status": "completed",
                "message": "Mock sync completed - Shopify module not available",
                "details": {
                    "total_products": 42,
                    "updated_products": 12,
                    "new_products": 3
                },
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        # Log sync failure
        logger.error(f"Sync failed for shop: {shop if 'shop' in locals() else 'unknown'} [action=sync_failed]", exc_info=e)
        
        return {
            "status": "failed",
            "message": f"Sync failed: {str(e)}",
            "error_type": type(e).__name__,
            "timestamp": datetime.now().isoformat()
        }