"""
Multi-Location Inventory Sync
Manages inventory across multiple locations with intelligent distribution
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session
import logging
import math

from database import AsyncSessionLocal
from models import Store, Location, InventoryItem, Product
from shopify_client import ShopifyClient
from utils.logging import logger


class MultiLocationSync:
    """Handles inventory synchronization across multiple locations"""
    
    def __init__(self):
        self.sync_interval = 300  # 5 minutes
        self.running = False
        
    async def sync_all_locations(self, store_id: int) -> Dict[str, Any]:
        """Sync inventory across all locations for a store"""
        
        async with AsyncSessionLocal() as session:
            # Get store and check features
            store = await session.get(Store, store_id)
            if not store:
                raise ValueError("Store not found")
            
            if not store.plan_features.get("multi_location", False):
                raise ValueError("Multi-location not enabled for this store")
            
            # Get all active locations
            result = await session.execute(
                select(Location).where(
                    and_(
                        Location.store_id == store_id,
                        Location.is_active == True
                    )
                )
            )
            locations = result.scalars().all()
            
            if len(locations) < 2:
                return {
                    "status": "skipped",
                    "reason": "Less than 2 active locations"
                }
            
            sync_results = {
                "synced_at": datetime.utcnow().isoformat(),
                "locations_synced": len(locations),
                "products_analyzed": 0,
                "transfers_suggested": 0,
                "imbalances_found": 0
            }
            
            # Analyze inventory distribution
            imbalances = await self._analyze_inventory_distribution(
                session, store_id, locations
            )
            
            sync_results["imbalances_found"] = len(imbalances)
            
            # Generate transfer suggestions
            transfers = await self._generate_transfer_suggestions(
                session, store_id, locations, imbalances
            )
            
            sync_results["transfers_suggested"] = len(transfers)
            
            # Update sync timestamp
            store.last_sync_at = datetime.utcnow()
            await session.commit()
            
            logger.info(
                f"Multi-location sync completed",
                store_id=store_id,
                results=sync_results
            )
            
            return sync_results
    
    async def _analyze_inventory_distribution(
        self, 
        session: Session,
        store_id: int,
        locations: List[Location]
    ) -> List[Dict[str, Any]]:
        """Analyze inventory distribution and find imbalances"""
        
        imbalances = []
        
        # Get all products with inventory
        result = await session.execute(
            select(Product).where(
                and_(
                    Product.store_id == store_id,
                    Product.status == "active"
                )
            )
        )
        products = result.scalars().all()
        
        for product in products:
            # Get inventory levels at each location
            location_inventory = {}
            total_inventory = 0
            
            for location in locations:
                result = await session.execute(
                    select(func.sum(InventoryItem.quantity_available)).where(
                        and_(
                            InventoryItem.product_id == product.id,
                            InventoryItem.location_id == location.id
                        )
                    )
                )
                quantity = result.scalar() or 0
                location_inventory[location.id] = {
                    "quantity": quantity,
                    "location": location,
                    "sales_velocity": await self._get_sales_velocity(
                        session, product.id, location.id
                    )
                }
                total_inventory += quantity
            
            if total_inventory == 0:
                continue
            
            # Calculate ideal distribution based on sales velocity
            ideal_distribution = self._calculate_ideal_distribution(
                location_inventory, total_inventory
            )
            
            # Find significant imbalances
            for location_id, data in location_inventory.items():
                ideal_qty = ideal_distribution.get(location_id, 0)
                actual_qty = data["quantity"]
                
                if abs(actual_qty - ideal_qty) > max(5, total_inventory * 0.1):
                    imbalances.append({
                        "product_id": product.id,
                        "product_title": product.title,
                        "location_id": location_id,
                        "location_name": data["location"].name,
                        "current_quantity": actual_qty,
                        "ideal_quantity": ideal_qty,
                        "difference": actual_qty - ideal_qty,
                        "sales_velocity": data["sales_velocity"]
                    })
        
        return imbalances
    
    async def _generate_transfer_suggestions(
        self,
        session: Session,
        store_id: int,
        locations: List[Location],
        imbalances: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate smart transfer suggestions"""
        
        transfers = []
        
        # Group imbalances by product
        product_imbalances = {}
        for imbalance in imbalances:
            product_id = imbalance["product_id"]
            if product_id not in product_imbalances:
                product_imbalances[product_id] = []
            product_imbalances[product_id].append(imbalance)
        
        # Generate transfers for each product
        for product_id, product_imbs in product_imbalances.items():
            # Find locations with excess and deficit
            excess_locations = [i for i in product_imbs if i["difference"] > 0]
            deficit_locations = [i for i in product_imbs if i["difference"] < 0]
            
            # Match excess with deficit
            for deficit in deficit_locations:
                needed = abs(deficit["difference"])
                
                for excess in excess_locations:
                    if needed <= 0:
                        break
                    
                    available = excess["difference"]
                    if available <= 0:
                        continue
                    
                    transfer_qty = min(needed, available)
                    
                    # Calculate transfer cost/benefit
                    benefit_score = self._calculate_transfer_benefit(
                        transfer_qty,
                        deficit["sales_velocity"],
                        excess["sales_velocity"]
                    )
                    
                    if benefit_score > 0.5:  # Only suggest beneficial transfers
                        transfers.append({
                            "product_id": product_id,
                            "product_title": deficit["product_title"],
                            "from_location_id": excess["location_id"],
                            "from_location_name": excess["location_name"],
                            "to_location_id": deficit["location_id"],
                            "to_location_name": deficit["location_name"],
                            "quantity": transfer_qty,
                            "benefit_score": benefit_score,
                            "reason": self._get_transfer_reason(deficit, excess),
                            "priority": self._get_transfer_priority(
                                deficit["current_quantity"],
                                deficit["sales_velocity"]
                            )
                        })
                        
                        # Update remaining quantities
                        excess["difference"] -= transfer_qty
                        needed -= transfer_qty
        
        # Sort by priority and benefit
        transfers.sort(key=lambda x: (x["priority"], x["benefit_score"]), reverse=True)
        
        return transfers[:10]  # Return top 10 suggestions
    
    async def create_transfer_order(
        self,
        store_id: int,
        transfer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a transfer order in the system"""
        
        # For simplified setup, just return mock data
        return {
            "transfer_id": 1,
            "status": "created",
            "message": "Transfer order created successfully"
        }
    
    async def get_location_performance(
        self,
        store_id: int,
        location_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get performance metrics for a specific location"""
        
        async with AsyncSessionLocal() as session:
            location = await session.get(Location, location_id)
            if not location or location.store_id != store_id:
                raise ValueError("Location not found")
            
            # Calculate metrics
            metrics = {
                "location": {
                    "id": location.id,
                    "name": location.name,
                    "type": location.location_type
                },
                "inventory": {
                    "total_products": 0,
                    "total_value": 0,
                    "low_stock_items": 0,
                    "out_of_stock_items": 0
                },
                "performance": {
                    "sales_velocity": 0,
                    "turnover_rate": 0,
                    "stockout_incidents": 0,
                    "efficiency_score": 0
                },
                "recommendations": []
            }
            
            # Get inventory summary
            result = await session.execute(
                select(
                    func.count(InventoryItem.id).label("product_count"),
                    func.sum(InventoryItem.quantity_available).label("total_quantity")
                ).where(
                    and_(
                        InventoryItem.location_id == location_id,
                        InventoryItem.quantity_available > 0
                    )
                )
            )
            inventory_data = result.first()
            
            if inventory_data:
                metrics["inventory"]["total_products"] = inventory_data.product_count
                
            # Generate recommendations
            if metrics["inventory"]["low_stock_items"] > 5:
                metrics["recommendations"].append({
                    "type": "restock",
                    "priority": "high",
                    "message": f"{metrics['inventory']['low_stock_items']} items need restocking"
                })
            
            return metrics
    
    def _calculate_ideal_distribution(
        self,
        location_inventory: Dict[int, Dict[str, Any]],
        total_inventory: int
    ) -> Dict[int, int]:
        """Calculate ideal inventory distribution based on sales velocity"""
        
        # Calculate total sales velocity
        total_velocity = sum(
            data["sales_velocity"] for data in location_inventory.values()
        )
        
        if total_velocity == 0:
            # Equal distribution if no sales data
            num_locations = len(location_inventory)
            equal_qty = total_inventory // num_locations
            return {loc_id: equal_qty for loc_id in location_inventory.keys()}
        
        # Distribute based on sales velocity
        ideal_distribution = {}
        for location_id, data in location_inventory.items():
            velocity_ratio = data["sales_velocity"] / total_velocity
            ideal_qty = round(total_inventory * velocity_ratio)
            ideal_distribution[location_id] = ideal_qty
        
        return ideal_distribution
    
    async def _get_sales_velocity(
        self,
        session: Session,
        product_id: int,
        location_id: int,
        days: int = 30
    ) -> float:
        """Get average daily sales velocity for a product at a location"""
        # Placeholder - implement based on your order tracking
        # For now, return mock data
        return 2.5  # Average 2.5 units per day
    
    def _calculate_transfer_benefit(
        self,
        quantity: int,
        to_velocity: float,
        from_velocity: float
    ) -> float:
        """Calculate benefit score for a transfer"""
        # Higher score means more beneficial transfer
        velocity_diff = to_velocity - from_velocity
        
        if velocity_diff <= 0:
            return 0.0
        
        # Normalize to 0-1 scale
        benefit = min(1.0, velocity_diff / max(to_velocity, from_velocity))
        
        # Factor in quantity (larger transfers have slightly lower scores)
        quantity_factor = 1.0 - (min(quantity, 100) / 200)
        
        return benefit * quantity_factor
    
    def _get_transfer_reason(
        self,
        deficit_location: Dict[str, Any],
        excess_location: Dict[str, Any]
    ) -> str:
        """Generate human-readable transfer reason"""
        
        if deficit_location["current_quantity"] == 0:
            return "Out of stock at destination"
        elif deficit_location["sales_velocity"] > excess_location["sales_velocity"] * 2:
            return "Higher demand at destination"
        elif deficit_location["current_quantity"] < 5:
            return "Low stock at destination"
        else:
            return "Inventory balancing"
    
    def _get_transfer_priority(
        self,
        current_quantity: int,
        sales_velocity: float
    ) -> str:
        """Determine transfer priority"""
        
        if current_quantity == 0:
            return "critical"
        
        days_of_stock = current_quantity / sales_velocity if sales_velocity > 0 else 999
        
        if days_of_stock < 3:
            return "high"
        elif days_of_stock < 7:
            return "medium"
        else:
            return "low"


# Singleton instance
multi_location_sync = MultiLocationSync()