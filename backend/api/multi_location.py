"""
Multi-Location Inventory Management API
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from pydantic import BaseModel

from multi_location_sync import multi_location_sync
from utils.logging import logger

router = APIRouter(prefix="/api/v1/locations", tags=["multi-location"])

class TransferRequest(BaseModel):
    """Request model for creating transfer orders"""
    product_id: int
    from_location_id: int
    to_location_id: int
    quantity: int
    notes: str = ""

@router.post("/{store_id}/sync")
async def sync_locations(store_id: int):
    """
    Sync inventory across all locations for a store
    Analyzes distribution and generates transfer suggestions
    """
    try:
        result = await multi_location_sync.sync_all_locations(store_id)
        logger.info(f"Multi-location sync completed for store {store_id}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to sync locations: {str(e)}", exc_info=e)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{store_id}/performance/{location_id}")
async def get_location_performance(
    store_id: int,
    location_id: int,
    days: int = 30
):
    """
    Get performance metrics for a specific location
    """
    try:
        metrics = await multi_location_sync.get_location_performance(
            store_id, location_id, days
        )
        return metrics
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get location performance: {str(e)}", exc_info=e)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{store_id}/transfers")
async def create_transfer_order(
    store_id: int,
    transfer: TransferRequest
):
    """
    Create a transfer order between locations
    """
    try:
        result = await multi_location_sync.create_transfer_order(
            store_id,
            transfer.dict()
        )
        logger.info(f"Transfer order created for store {store_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to create transfer order: {str(e)}", exc_info=e)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{store_id}/distribution")
async def get_inventory_distribution(store_id: int):
    """
    Get current inventory distribution across all locations
    Returns a breakdown of products and their quantities at each location
    """
    # Mock data for now - integrate with actual database later
    return {
        "store_id": store_id,
        "locations": [
            {
                "id": 1,
                "name": "Main Warehouse",
                "type": "warehouse",
                "total_products": 150,
                "total_value": 45000,
                "inventory_breakdown": {
                    "in_stock": 120,
                    "low_stock": 25,
                    "out_of_stock": 5
                }
            },
            {
                "id": 2,
                "name": "Downtown Store",
                "type": "retail",
                "total_products": 85,
                "total_value": 23000,
                "inventory_breakdown": {
                    "in_stock": 65,
                    "low_stock": 18,
                    "out_of_stock": 2
                }
            },
            {
                "id": 3,
                "name": "Airport Kiosk",
                "type": "retail",
                "total_products": 45,
                "total_value": 12000,
                "inventory_breakdown": {
                    "in_stock": 35,
                    "low_stock": 8,
                    "out_of_stock": 2
                }
            }
        ],
        "total_inventory_value": 80000,
        "recommendations": [
            {
                "type": "transfer",
                "priority": "high",
                "message": "Transfer 20 units of 'Blue T-Shirt (M)' from Main Warehouse to Downtown Store"
            },
            {
                "type": "restock",
                "priority": "medium",
                "message": "Restock 'Red Sneakers (42)' at all locations - currently out of stock"
            }
        ]
    }

@router.get("/{store_id}/transfers/suggestions")
async def get_transfer_suggestions(store_id: int):
    """
    Get AI-powered transfer suggestions based on sales velocity and stock levels
    """
    # Mock data showing intelligent transfer suggestions
    return {
        "store_id": store_id,
        "generated_at": "2025-07-11T18:20:00Z",
        "suggestions": [
            {
                "id": 1,
                "product": "Blue T-Shirt (M)",
                "from_location": "Main Warehouse",
                "to_location": "Downtown Store",
                "quantity": 15,
                "reason": "High sales velocity at destination, excess stock at source",
                "benefit_score": 0.85,
                "priority": "high",
                "estimated_impact": "Prevents stockout in 3 days"
            },
            {
                "id": 2,
                "product": "Green Hat",
                "from_location": "Main Warehouse",
                "to_location": "Airport Kiosk",
                "quantity": 10,
                "reason": "Low stock at destination, seasonal demand increase",
                "benefit_score": 0.72,
                "priority": "medium",
                "estimated_impact": "Maintains optimal stock levels"
            },
            {
                "id": 3,
                "product": "Wireless Earbuds",
                "from_location": "Downtown Store",
                "to_location": "Main Warehouse",
                "quantity": 5,
                "reason": "Overstock at source, centralize slow-moving inventory",
                "benefit_score": 0.65,
                "priority": "low",
                "estimated_impact": "Improves inventory turnover"
            }
        ],
        "summary": {
            "total_suggestions": 3,
            "high_priority": 1,
            "potential_stockouts_prevented": 2,
            "estimated_value_optimized": 5400
        }
    }

@router.get("/{store_id}/analytics")
async def get_location_analytics(store_id: int):
    """
    Get advanced analytics for multi-location inventory
    """
    return {
        "store_id": store_id,
        "period": "last_30_days",
        "location_performance": [
            {
                "location": "Main Warehouse",
                "metrics": {
                    "inventory_turnover": 4.2,
                    "stockout_rate": 2.1,
                    "transfer_efficiency": 92.5,
                    "carrying_cost": 3200
                }
            },
            {
                "location": "Downtown Store",
                "metrics": {
                    "inventory_turnover": 6.8,
                    "stockout_rate": 4.5,
                    "transfer_efficiency": 88.3,
                    "carrying_cost": 1800
                }
            }
        ],
        "optimization_opportunities": [
            {
                "type": "redistribute",
                "impact": "high",
                "description": "Redistribute slow-moving items from retail to warehouse",
                "potential_savings": 1200
            },
            {
                "type": "consolidate",
                "impact": "medium",
                "description": "Consolidate duplicate SKUs across locations",
                "potential_savings": 800
            }
        ],
        "insights": [
            "Downtown Store has 62% higher turnover than warehouse",
            "Airport Kiosk shows seasonal patterns - increase stock before holidays",
            "Transfer lead time averaging 2.3 days - consider express transfers for urgent items"
        ]
    }
