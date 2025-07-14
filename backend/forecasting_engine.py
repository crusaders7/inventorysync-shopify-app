"""
AI-Powered Forecasting Engine
Predicts inventory needs based on sales patterns
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session
import logging

from database import AsyncSessionLocal
from models import Store, Product, InventoryItem

logger = logging.getLogger(__name__)


class ForecastingEngine:
    """Advanced inventory forecasting using statistical methods"""
    
    def __init__(self):
        self.seasonality_factors = {
            "Q1": 0.85,  # Jan-Mar (typically slower)
            "Q2": 1.0,   # Apr-Jun (baseline)
            "Q3": 0.95,  # Jul-Sep
            "Q4": 1.2    # Oct-Dec (holiday season)
        }
    
    async def forecast_demand(
        self, 
        store_id: int, 
        product_id: int,
        days_ahead: int = 30,
        include_seasonality: bool = True
    ) -> Dict[str, Any]:
        """Forecast demand for a specific product"""
        
        async with AsyncSessionLocal() as session:
            # Get historical sales data
            sales_history = await self._get_sales_history(
                session, store_id, product_id, days_back=90
            )
            
            if not sales_history:
                return {
                    "forecast": 0,
                    "confidence": 0,
                    "method": "no_data",
                    "recommendation": "Insufficient data for forecasting"
                }
            
            # Calculate basic metrics
            daily_sales = [s["quantity"] for s in sales_history]
            avg_daily_sales = np.mean(daily_sales)
            std_daily_sales = np.std(daily_sales)
            
            # Detect trend
            trend = self._calculate_trend(daily_sales)
            
            # Apply seasonality if enabled
            if include_seasonality:
                current_quarter = f"Q{(datetime.now().month - 1) // 3 + 1}"
                seasonality_factor = self.seasonality_factors.get(current_quarter, 1.0)
            else:
                seasonality_factor = 1.0
            
            # Calculate forecast
            base_forecast = avg_daily_sales * days_ahead
            trend_adjustment = trend * days_ahead * avg_daily_sales
            seasonal_adjustment = (seasonality_factor - 1) * base_forecast
            
            forecast = base_forecast + trend_adjustment + seasonal_adjustment
            
            # Calculate confidence interval
            confidence_interval = 1.96 * std_daily_sales * np.sqrt(days_ahead)
            
            # Get current inventory
            current_inventory = await self._get_current_inventory(
                session, store_id, product_id
            )
            
            # Calculate reorder point
            lead_time_days = 7  # Default lead time
            safety_stock = 2 * std_daily_sales * np.sqrt(lead_time_days)
            reorder_point = (avg_daily_sales * lead_time_days) + safety_stock
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                forecast, current_inventory, reorder_point, avg_daily_sales
            )
            
            return {
                "forecast": round(forecast, 2),
                "confidence_interval": {
                    "lower": round(max(0, forecast - confidence_interval), 2),
                    "upper": round(forecast + confidence_interval, 2)
                },
                "confidence": self._calculate_confidence_score(daily_sales),
                "method": "time_series_analysis",
                "metrics": {
                    "avg_daily_sales": round(avg_daily_sales, 2),
                    "std_deviation": round(std_daily_sales, 2),
                    "trend": round(trend, 4),
                    "seasonality_factor": seasonality_factor
                },
                "inventory": {
                    "current": current_inventory,
                    "reorder_point": round(reorder_point, 2),
                    "safety_stock": round(safety_stock, 2),
                    "days_of_supply": round(current_inventory / avg_daily_sales, 1) if avg_daily_sales > 0 else 0
                },
                "recommendations": recommendations
            }
    
    async def forecast_all_products(
        self, 
        store_id: int,
        days_ahead: int = 30
    ) -> List[Dict[str, Any]]:
        """Forecast demand for all active products"""
        
        async with AsyncSessionLocal() as session:
            # Get all active products
            result = await session.execute(
                select(Product).where(
                    and_(
                        Product.store_id == store_id,
                        Product.status == "active"
                    )
                )
            )
            products = result.scalars().all()
            
            forecasts = []
            for product in products:
                forecast = await self.forecast_demand(
                    store_id, product.id, days_ahead
                )
                forecast["product"] = {
                    "id": product.id,
                    "title": product.title,
                    "sku": product.variants[0].sku if product.variants else None
                }
                forecasts.append(forecast)
            
            # Sort by urgency (lowest days of supply first)
            forecasts.sort(
                key=lambda x: x["inventory"]["days_of_supply"]
            )
            
            return forecasts
    
    async def detect_anomalies(
        self, 
        store_id: int,
        sensitivity: float = 2.5
    ) -> List[Dict[str, Any]]:
        """Detect unusual sales patterns or inventory levels"""
        
        anomalies = []
        
        async with AsyncSessionLocal() as session:
            # Get recent sales data for all products
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            result = await session.execute(
                select(
                    Product.id,
                    Product.title,
                    func.sum(OrderItem.quantity).label("total_sold"),
                    func.count(OrderItem.id).label("order_count")
                ).join(
                    OrderItem, OrderItem.product_id == Product.id
                ).where(
                    and_(
                        Product.store_id == store_id,
                        OrderItem.created_at >= thirty_days_ago
                    )
                ).group_by(Product.id)
            )
            
            recent_sales = result.all()
            
            for product_id, title, total_sold, order_count in recent_sales:
                # Get historical average
                historical_avg = await self._get_historical_average(
                    session, store_id, product_id, days=90
                )
                
                if historical_avg > 0:
                    deviation = (total_sold - historical_avg) / historical_avg
                    
                    if abs(deviation) > sensitivity:
                        anomalies.append({
                            "product_id": product_id,
                            "product_title": title,
                            "type": "sales_spike" if deviation > 0 else "sales_drop",
                            "severity": "high" if abs(deviation) > sensitivity * 2 else "medium",
                            "current_sales": total_sold,
                            "expected_sales": historical_avg,
                            "deviation_percentage": round(deviation * 100, 2),
                            "recommendation": self._get_anomaly_recommendation(deviation)
                        })
        
        return anomalies
    
    def _calculate_trend(self, data: List[float]) -> float:
        """Calculate linear trend in the data"""
        if len(data) < 2:
            return 0.0
        
        x = np.arange(len(data))
        y = np.array(data)
        
        # Simple linear regression
        slope = np.polyfit(x, y, 1)[0]
        avg_value = np.mean(y)
        
        # Normalize trend as percentage of average
        return slope / avg_value if avg_value > 0 else 0.0
    
    def _calculate_confidence_score(self, data: List[float]) -> float:
        """Calculate confidence score based on data consistency"""
        if len(data) < 7:
            return 0.3
        
        cv = np.std(data) / np.mean(data) if np.mean(data) > 0 else 1.0
        
        # Lower CV means more consistent data, higher confidence
        if cv < 0.2:
            return 0.95
        elif cv < 0.5:
            return 0.85
        elif cv < 1.0:
            return 0.70
        else:
            return 0.50
    
    async def _get_sales_history(
        self, 
        session: Session,
        store_id: int,
        product_id: int,
        days_back: int
    ) -> List[Dict[str, Any]]:
        """Get historical sales data"""
        start_date = datetime.now() - timedelta(days=days_back)
        
        # This is a placeholder - implement based on your order tracking
        # For now, generate sample data
        sales_data = []
        for i in range(days_back):
            date = start_date + timedelta(days=i)
            # Simulate sales with some randomness
            base_sales = 10
            random_factor = np.random.normal(1.0, 0.3)
            quantity = max(0, int(base_sales * random_factor))
            
            sales_data.append({
                "date": date,
                "quantity": quantity
            })
        
        return sales_data
    
    async def _get_current_inventory(
        self,
        session: Session,
        store_id: int,
        product_id: int
    ) -> int:
        """Get current inventory level"""
        result = await session.execute(
            select(func.sum(InventoryItem.quantity_available)).where(
                and_(
                    InventoryItem.product_id == product_id,
                    InventoryItem.store_id == store_id
                )
            )
        )
        return result.scalar() or 0
    
    async def _get_historical_average(
        self,
        session: Session,
        store_id: int,
        product_id: int,
        days: int
    ) -> float:
        """Get historical average sales"""
        # Placeholder implementation
        return 10.0  # Return sample average
    
    def _generate_recommendations(
        self,
        forecast: float,
        current_inventory: int,
        reorder_point: float,
        avg_daily_sales: float
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Check if reorder needed
        if current_inventory <= reorder_point:
            order_quantity = forecast - current_inventory + reorder_point
            recommendations.append(
                f"⚠️ Reorder immediately: Order {round(order_quantity)} units to meet forecasted demand"
            )
        
        # Check days of supply
        days_of_supply = current_inventory / avg_daily_sales if avg_daily_sales > 0 else 0
        
        if days_of_supply < 7:
            recommendations.append(
                "🚨 Critical: Less than 1 week of inventory remaining"
            )
        elif days_of_supply < 14:
            recommendations.append(
                "⚡ Low stock: Consider expedited shipping for next order"
            )
        elif days_of_supply > 90:
            recommendations.append(
                "📦 Overstocked: Consider promotions to reduce inventory"
            )
        
        # Seasonal recommendations
        current_month = datetime.now().month
        if current_month in [10, 11]:  # Pre-holiday
            recommendations.append(
                "🎄 Holiday season approaching: Consider increasing safety stock"
            )
        
        return recommendations
    
    def _get_anomaly_recommendation(self, deviation: float) -> str:
        """Get recommendation for anomaly"""
        if deviation > 2:
            return "Investigate cause of sales spike and ensure adequate inventory"
        elif deviation > 1:
            return "Monitor closely and consider increasing reorder quantity"
        elif deviation < -2:
            return "Review marketing efforts and consider promotions"
        elif deviation < -1:
            return "Analyze competition and adjust pricing if needed"
        else:
            return "Continue monitoring"


# Singleton instance
forecasting_engine = ForecastingEngine()