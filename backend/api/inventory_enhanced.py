"""
Enhanced Inventory Management API with Pagination and Caching
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from database import get_async_db
from models import InventoryItem, ProductVariant, Product, Location, Store
from utils.cache import cache, cached
from utils.logging import logger
from api.auth import get_current_store

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=50, ge=1, le=250, description="Items per page")
    cursor: Optional[str] = Field(default=None, description="Cursor for cursor-based pagination")


class InventoryItemResponse(BaseModel):
    """Inventory item response model"""
    id: int
    variant_id: int
    location_id: int
    sku: Optional[str]
    product_name: str
    variant_title: str
    location_name: str
    available_quantity: int
    committed_quantity: int
    on_hand_quantity: int
    reorder_point: int
    reorder_quantity: int
    lead_time_days: int
    status: str
    custom_data: Dict[str, Any]
    last_updated: datetime

    class Config:
        orm_mode = True


class PaginatedResponse(BaseModel):
    """Paginated response with metadata"""
    items: List[InventoryItemResponse]
    pagination: Dict[str, Any]
    total: int
    filters: Dict[str, Any]


@router.get("", response_model=PaginatedResponse)
@cached(ttl=60, key_prefix="inventory:list")
async def list_inventory(
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=250, description="Items per page"),
    cursor: Optional[str] = Query(None, description="Cursor for next page"),
    
    # Filters
    location_id: Optional[int] = Query(None, description="Filter by location ID"),
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    variant_id: Optional[int] = Query(None, description="Filter by variant ID"),
    sku: Optional[str] = Query(None, description="Filter by SKU"),
    status: Optional[str] = Query(None, description="Filter by status (low_stock, out_of_stock, overstock)"),
    search: Optional[str] = Query(None, description="Search in product names and SKUs"),
    
    # Sorting
    sort_by: str = Query("updated_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    
    # Database session
    db: AsyncSession = Depends(get_async_db),
    store: Store = Depends(get_current_store)
):
    """
    List inventory items with advanced filtering and pagination
    
    Features:
    - Cursor-based pagination for large datasets
    - Multiple filter options
    - Full-text search
    - Custom sorting
    - Response caching
    """
    try:
        # Build base query
        query = (
            select(
                InventoryItem,
                ProductVariant.sku,
                ProductVariant.title.label("variant_title"),
                Product.title.label("product_name"),
                Location.name.label("location_name")
            )
            .join(ProductVariant, InventoryItem.variant_id == ProductVariant.id)
            .join(Product, ProductVariant.product_id == Product.id)
            .join(Location, InventoryItem.location_id == Location.id)
            .where(InventoryItem.store_id == store.id)
        )
        
        # Apply filters
        filters = []
        
        if location_id:
            filters.append(InventoryItem.location_id == location_id)
        
        if product_id:
            filters.append(Product.id == product_id)
        
        if variant_id:
            filters.append(InventoryItem.variant_id == variant_id)
        
        if sku:
            filters.append(ProductVariant.sku.ilike(f"%{sku}%"))
        
        if status:
            if status == "low_stock":
                filters.append(
                    and_(
                        InventoryItem.available_quantity < InventoryItem.reorder_point,
                        InventoryItem.available_quantity > 0
                    )
                )
            elif status == "out_of_stock":
                filters.append(InventoryItem.available_quantity == 0)
            elif status == "overstock":
                filters.append(
                    InventoryItem.available_quantity > InventoryItem.reorder_point * 5
                )
        
        if search:
            search_term = f"%{search}%"
            filters.append(
                or_(
                    Product.title.ilike(search_term),
                    ProductVariant.sku.ilike(search_term),
                    ProductVariant.title.ilike(search_term)
                )
            )
        
        if filters:
            query = query.where(and_(*filters))
        
        # Apply cursor-based pagination if cursor provided
        if cursor:
            # Decode cursor (in production, use proper encoding)
            try:
                cursor_value = int(cursor)
                query = query.where(InventoryItem.id > cursor_value)
            except:
                pass
        
        # Apply sorting
        sort_column = getattr(InventoryItem, sort_by, InventoryItem.updated_at)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Add secondary sort by ID for stable pagination
        query = query.order_by(InventoryItem.id.asc())
        
        # Execute count query for total
        count_query = select(func.count()).select_from(InventoryItem).where(InventoryItem.store_id == store.id)
        if filters:
            count_query = count_query.where(and_(*filters))
        
        total_result = await db.execute(count_query)
        total_count = total_result.scalar() or 0
        
        # Apply limit for pagination
        query = query.limit(limit + 1)  # Fetch one extra to check if there's a next page
        
        # Apply offset for page-based pagination (if not using cursor)
        if not cursor:
            offset = (page - 1) * limit
            query = query.offset(offset)
        
        # Execute main query
        result = await db.execute(query)
        rows = result.all()
        
        # Check if there's a next page
        has_next_page = len(rows) > limit
        if has_next_page:
            rows = rows[:-1]  # Remove the extra item
        
        # Build response items
        items = []
        last_id = None
        
        for row in rows:
            item = row.InventoryItem
            
            # Determine status
            if item.available_quantity == 0:
                status_str = "out_of_stock"
            elif item.available_quantity < item.reorder_point:
                status_str = "low_stock"
            elif item.available_quantity > item.reorder_point * 5:
                status_str = "overstock"
            else:
                status_str = "normal"
            
            items.append(InventoryItemResponse(
                id=item.id,
                variant_id=item.variant_id,
                location_id=item.location_id,
                sku=row.sku,
                product_name=row.product_name,
                variant_title=row.variant_title,
                location_name=row.location_name,
                available_quantity=item.available_quantity,
                committed_quantity=item.committed_quantity,
                on_hand_quantity=item.on_hand_quantity,
                reorder_point=item.reorder_point,
                reorder_quantity=item.reorder_quantity,
                lead_time_days=item.lead_time_days,
                status=status_str,
                custom_data=item.custom_data or {},
                last_updated=item.updated_at
            ))
            
            last_id = item.id
        
        # Build pagination metadata
        pagination_meta = {
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit,
            "has_next_page": has_next_page,
            "has_previous_page": page > 1 if not cursor else bool(cursor),
            "next_cursor": str(last_id) if has_next_page and last_id else None
        }
        
        # Build filter summary
        applied_filters = {
            "location_id": location_id,
            "product_id": product_id,
            "variant_id": variant_id,
            "sku": sku,
            "status": status,
            "search": search,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        
        logger.info(
            f"Inventory query completed for store {store.id}",
            extra={
                "store_id": store.id,
                "total_results": total_count,
                "page": page,
                "limit": limit,
                "filters": applied_filters
            }
        )
        
        return PaginatedResponse(
            items=items,
            pagination=pagination_meta,
            total=total_count,
            filters=applied_filters
        )
        
    except Exception as e:
        logger.error(f"Failed to list inventory: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve inventory")


@router.post("/bulk-update")
async def bulk_update_inventory(
    updates: List[Dict[str, Any]],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    store: Store = Depends(get_current_store)
):
    """
    Bulk update inventory levels with background processing
    
    Accepts a list of updates:
    [
        {
            "variant_id": 123,
            "location_id": 456,
            "available_quantity": 100
        },
        ...
    ]
    """
    try:
        # Validate update count
        if len(updates) > 1000:
            raise HTTPException(
                status_code=400,
                detail="Maximum 1000 items can be updated at once"
            )
        
        # Queue background task for processing
        background_tasks.add_task(
            process_bulk_inventory_update,
            store_id=store.id,
            updates=updates
        )
        
        # Invalidate relevant caches
        await cache.delete_pattern(f"inventory:list:*")
        await cache.delete_pattern(f"dashboard:*:inventory*")
        
        return {
            "message": f"Bulk update queued for {len(updates)} items",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Failed to queue bulk update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process bulk update")


async def process_bulk_inventory_update(store_id: int, updates: List[Dict[str, Any]]):
    """Background task to process bulk inventory updates"""
    async with AsyncSessionLocal() as db:
        try:
            for update in updates:
                variant_id = update.get("variant_id")
                location_id = update.get("location_id")
                new_quantity = update.get("available_quantity")
                
                if not all([variant_id, location_id, new_quantity is not None]):
                    continue
                
                # Find and update inventory item
                result = await db.execute(
                    select(InventoryItem).where(
                        and_(
                            InventoryItem.store_id == store_id,
                            InventoryItem.variant_id == variant_id,
                            InventoryItem.location_id == location_id
                        )
                    )
                )
                item = result.scalar_one_or_none()
                
                if item:
                    old_quantity = item.available_quantity
                    item.available_quantity = new_quantity
                    item.on_hand_quantity = new_quantity - item.committed_quantity
                    
                    # Log the change
                    logger.info(
                        f"Inventory updated: variant={variant_id}, location={location_id}, "
                        f"old_qty={old_quantity}, new_qty={new_quantity}"
                    )
            
            await db.commit()
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Bulk inventory update failed: {str(e)}", exc_info=True)
