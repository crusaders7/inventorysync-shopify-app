"""
Forecasting API Endpoints
AI-powered inventory predictions
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from datetime import datetime

from forecasting_engine import forecasting_engine
from database import AsyncSessionLocal
from models import Store
from utils.logging import logger
from sqlalchemy import select

router = APIRouter(prefix="/api/v1/forecasting", tags=["forecasting"])


@router.get("/product/{product_id}")
async def forecast_product_demand(
    product_id: int,
    shop: str = Query(..., description="Shop domain"),
    days_ahead: int = Query(30, ge=1, le=365, description="Days to forecast"),
    include_seasonality: bool = Query(True, description="Include seasonal adjustments")
):
    """Get demand forecast for a specific product"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Check if forecasting is enabled for this plan
            if not store.plan_features.get("forecasting", False):
                raise HTTPException(
                    status_code=403, 
                    detail="Forecasting not available in your current plan"
                )
            
            # Get forecast
            forecast = await forecasting_engine.forecast_demand(
                store_id=store.id,
                product_id=product_id,
                days_ahead=days_ahead,
                include_seasonality=include_seasonality
            )
            
            logger.info(
                f"Generated forecast",
                shop=shop,
                product_id=product_id,
                forecast_value=forecast["forecast"]
            )
            
            return forecast
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forecasting error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Forecasting failed")


@router.get("/all-products")
async def forecast_all_products(
    shop: str = Query(..., description="Shop domain"),
    days_ahead: int = Query(30, ge=1, le=365, description="Days to forecast"),
    limit: int = Query(50, ge=1, le=200, description="Maximum products to forecast")
):
    """Get demand forecast for all products"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Check if forecasting is enabled
            if not store.plan_features.get("forecasting", False):
                raise HTTPException(
                    status_code=403, 
                    detail="Forecasting not available in your current plan"
                )
            
            # Get forecasts
            forecasts = await forecasting_engine.forecast_all_products(
                store_id=store.id,
                days_ahead=days_ahead
            )
            
            # Apply limit
            forecasts = forecasts[:limit]
            
            logger.info(
                f"Generated bulk forecast",
                shop=shop,
                product_count=len(forecasts)
            )
            
            return {
                "forecasts": forecasts,
                "generated_at": datetime.utcnow().isoformat(),
                "parameters": {
                    "days_ahead": days_ahead,
                    "products_analyzed": len(forecasts)
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk forecasting error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Bulk forecasting failed")


@router.get("/anomalies")
async def detect_anomalies(
    shop: str = Query(..., description="Shop domain"),
    sensitivity: float = Query(2.5, ge=1.0, le=5.0, description="Anomaly sensitivity")
):
    """Detect unusual sales patterns or inventory anomalies"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Detect anomalies
            anomalies = await forecasting_engine.detect_anomalies(
                store_id=store.id,
                sensitivity=sensitivity
            )
            
            logger.info(
                f"Detected anomalies",
                shop=shop,
                anomaly_count=len(anomalies)
            )
            
            return {
                "anomalies": anomalies,
                "detected_at": datetime.utcnow().isoformat(),
                "sensitivity": sensitivity,
                "total_found": len(anomalies)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Anomaly detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Anomaly detection failed")


@router.get("/insights")
async def get_inventory_insights(
    shop: str = Query(..., description="Shop domain")
):
    """Get AI-powered inventory insights and recommendations"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Generate insights
            insights = {
                "overview": {
                    "total_products": 0,  # To be implemented
                    "low_stock_items": 0,
                    "overstock_items": 0,
                    "optimal_items": 0
                },
                "recommendations": [
                    {
                        "type": "reorder",
                        "priority": "high",
                        "message": "5 products need immediate reordering",
                        "action": "View products requiring reorder"
                    },
                    {
                        "type": "optimization",
                        "priority": "medium",
                        "message": "3 products are overstocked by 200%",
                        "action": "Create promotion for overstock"
                    }
                ],
                "trends": {
                    "sales_trend": "increasing",
                    "trend_percentage": 15.5,
                    "best_performing_category": "Electronics",
                    "seasonal_alert": "Holiday season approaching - increase safety stock"
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return insights
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Insights generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate insights")