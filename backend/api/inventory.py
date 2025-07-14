"""
Inventory Management API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, validator
import logging

# Import validation utilities
from utils.validation import (
    ProductValidator, SKUValidator, StockValidator, 
    validate_pagination, validate_sort_params, sanitize_string
)
from utils.logging import logger
from utils.exceptions import validation_error, not_found_error

router = APIRouter()

# Mock data for now
mock_inventory = [
    {
        "id": "1",
        "product_name": "Blue T-Shirt (M)",
        "sku": "BTS-M-001",
        "current_stock": 5,
        "reorder_point": 10,
        "location": "Warehouse A",
        "status": "low_stock"
    },
    {
        "id": "2",
        "product_name": "Red Sneakers (42)",
        "sku": "RSN-42-001",
        "current_stock": 0,
        "reorder_point": 5,
        "location": "Warehouse B",
        "status": "out_of_stock"
    },
    {
        "id": "3",
        "product_name": "Green Hat",
        "sku": "GH-001",
        "current_stock": 150,
        "reorder_point": 20,
        "location": "Warehouse A",
        "status": "overstock"
    }
]

class CreateProductRequest(BaseModel):
    product_name: str
    sku: str
    current_stock: int
    reorder_point: int
    location: str = "Warehouse A"
    
    @validator('product_name')
    def validate_product_name(cls, v):
        return ProductValidator.validate_name(v)
    
    @validator('sku')
    def validate_sku(cls, v):
        return SKUValidator.validate(v)
    
    @validator('current_stock')
    def validate_current_stock(cls, v):
        return StockValidator.validate_quantity(v)
    
    @validator('reorder_point')
    def validate_reorder_point(cls, v):
        return StockValidator.validate_reorder_point(v)
    
    @validator('location')
    def validate_location(cls, v):
        return ProductValidator.validate_location(v)

class UpdateStockRequest(BaseModel):
    quantity: int
    
    @validator('quantity')
    def validate_quantity(cls, v):
        return StockValidator.validate_quantity(v)

@router.post("/")
async def create_product(product: CreateProductRequest):
    """
    Create a new inventory item
    """
    try:
        # Check for duplicate SKU
        existing_item = next((item for item in mock_inventory if item["sku"] == product.sku), None)
        if existing_item:
            raise validation_error(f"Product with SKU '{product.sku}' already exists")
        
        # Generate new ID
        new_id = str(len(mock_inventory) + 1)
        
        # Determine status
        status = "normal"
        if product.current_stock == 0:
            status = "out_of_stock"
        elif product.current_stock < product.reorder_point:
            status = "low_stock"
        elif product.current_stock > product.reorder_point * 5:
            status = "overstock"
        
        new_item = {
            "id": new_id,
            "product_name": product.product_name,
            "sku": product.sku,
            "current_stock": product.current_stock,
            "reorder_point": product.reorder_point,
            "location": product.location,
            "status": status
        }
        
        mock_inventory.append(new_item)
        
        # Log inventory action
        logger.info(
            f"Inventory action: create_product - Product ID: {new_id}, SKU: {product.sku}, Quantity: {product.current_stock}"
        )
        
        return {
            "message": "Product created successfully",
            "item": new_item
        }
        
    except Exception as e:
        logger.error(f"Failed to create product: {str(e)}", exc_info=e)
        raise

@router.get("/")
async def get_inventory_items(
    location: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1),
    limit: int = Query(20)
):
    """
    Get inventory items with optional filters and pagination
    """
    try:
        # Validate pagination
        page, limit = validate_pagination(page, limit)
        
        # Validate and sanitize search input
        if search:
            search = sanitize_string(search, max_length=100)
        
        # Validate status filter
        valid_statuses = ['normal', 'low_stock', 'out_of_stock', 'overstock']
        if status and status not in valid_statuses:
            raise validation_error(f"Invalid status. Must be one of: {valid_statuses}")
        
        # Validate location filter
        if location:
            location = sanitize_string(location, max_length=100)
        
        items = mock_inventory.copy()
        
        # Apply filters
        if location:
            items = [i for i in items if i["location"].lower() == location.lower()]
        
        if status:
            items = [i for i in items if i["status"] == status]
        
        if search:
            search_lower = search.lower()
            items = [i for i in items if search_lower in i["product_name"].lower() or search_lower in i["sku"].lower()]
        
        # Apply pagination
        total_items = len(items)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_items = items[start_idx:end_idx]
        
        # Log inventory query
        logger.info(
            f"Inventory query completed. Total results: {total_items}, Page: {page}, Limit: {limit}, Location filter: {location}, Status filter: {status}, Search query: {search}"
        )
        
        return {
            "items": paginated_items,
            "total": total_items,
            "page": page,
            "limit": limit,
            "total_pages": (total_items + limit - 1) // limit,
            "filters": {
                "location": location,
                "status": status,
                "search": search
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch inventory items: {str(e)}", exc_info=e)
        raise

@router.get("/locations")
async def get_locations():
    """
    Get all inventory locations
    """
    return {
        "locations": [
            {"id": "1", "name": "Warehouse A", "type": "warehouse"},
            {"id": "2", "name": "Warehouse B", "type": "warehouse"},
            {"id": "3", "name": "Retail Store", "type": "retail"}
        ]
    }

@router.get("/stats")
async def get_inventory_stats():
    """
    Get inventory statistics
    """
    return {
        "total_products": len(mock_inventory),
        "low_stock_count": len([i for i in mock_inventory if i["status"] == "low_stock"]),
        "out_of_stock_count": len([i for i in mock_inventory if i["status"] == "out_of_stock"]),
        "overstock_count": len([i for i in mock_inventory if i["status"] == "overstock"]),
        "total_value": 125430,
        "locations_count": 3
    }

@router.put("/{item_id}/stock")
async def update_stock_level(
    item_id: str,
    request: UpdateStockRequest
):
    """
    Update stock level for an inventory item
    """
    try:
        # Validate item_id format
        if not item_id or not item_id.isdigit():
            raise validation_error("Invalid item ID format")
        
        quantity = request.quantity
        old_quantity = None
        
        # Find item in mock data
        item = next((i for i in mock_inventory if i["id"] == item_id), None)
        
        if not item:
            raise not_found_error("Inventory item", item_id)
        
        # Store old quantity for logging
        old_quantity = item["current_stock"]
        
        # Update stock
        item["current_stock"] = quantity
        
        # Update status based on new quantity
        old_status = item["status"]
        if quantity == 0:
            item["status"] = "out_of_stock"
        elif quantity < item["reorder_point"]:
            item["status"] = "low_stock"
        elif quantity > item["reorder_point"] * 5:
            item["status"] = "overstock"
        else:
            item["status"] = "normal"
        
        # Log inventory action
        logger.info(
            f"Inventory action: update_stock - Product ID: {item_id}, SKU: {item['sku']}, Quantity: {quantity}, Old quantity: {old_quantity}, Old status: {old_status}, New status: {item['status']}"
        )
        
        return {
            "message": "Stock level updated successfully",
            "item": item,
            "changes": {
                "old_quantity": old_quantity,
                "new_quantity": quantity,
                "status_changed": old_status != item["status"]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to update stock for item {item_id}: {str(e)}", exc_info=e)
        raise