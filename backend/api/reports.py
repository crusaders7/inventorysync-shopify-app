"""
Custom Reports API - Build reports on any field
Advanced reporting engine with custom field support
"""

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, desc, func, case, distinct
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
import json
import csv
import io
from enum import Enum

from database import AsyncSessionLocal
from models import (
    Store, Product, ProductVariant, InventoryItem, 
    Location, Alert, CustomFieldDefinition
)
from utils.logging import logger

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class AggregationType(str, Enum):
    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    COUNT_DISTINCT = "count_distinct"


class GroupByType(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    LOCATION = "location"
    PRODUCT_TYPE = "product_type"
    VENDOR = "vendor"
    CUSTOM_FIELD = "custom_field"


class ReportMetric(BaseModel):
    field: str  # e.g., "available_quantity", "price", "custom_data.season"
    aggregation: AggregationType
    label: Optional[str] = None


class ReportFilter(BaseModel):
    field: str
    operator: str = Field(..., pattern="^(equals|not_equals|greater_than|less_than|contains|in|between)$")
    value: Union[str, int, float, List[Any]]


class ReportDefinition(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    entity_type: str = Field(..., pattern="^(product|variant|inventory|alert)$")
    metrics: List[ReportMetric] = Field(..., min_items=1)
    group_by: Optional[List[GroupByType]] = []
    filters: Optional[List[ReportFilter]] = []
    sort_by: Optional[str] = None
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")
    limit: int = Field(default=1000, ge=1, le=10000)


class SavedReport(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    definition: ReportDefinition
    is_public: bool = False
    schedule: Optional[str] = None  # cron expression
    export_format: str = Field(default="json", pattern="^(json|csv|excel)$")


# =============================================================================
# REPORT BUILDER ENDPOINTS
# =============================================================================

@router.post("/{shop_domain}/build")
async def build_custom_report(
    shop_domain: str,
    report_def: ReportDefinition,
    export_format: str = Query("json", pattern="^(json|csv|excel)$")
):
    """Build a custom report based on the provided definition"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop_domain)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Build and execute query based on entity type
            report_data = await execute_report_query(session, store.id, report_def)
            
            # Format response based on export format
            if export_format == "csv":
                return create_csv_response(report_data, report_def)
            elif export_format == "excel":
                # TODO: Implement Excel export
                raise HTTPException(status_code=501, detail="Excel export not yet implemented")
            else:
                return {
                    "report_name": report_def.name,
                    "generated_at": datetime.now().isoformat(),
                    "row_count": len(report_data),
                    "data": report_data,
                    "metadata": {
                        "entity_type": report_def.entity_type,
                        "metrics": [m.dict() for m in report_def.metrics],
                        "group_by": report_def.group_by,
                        "filters": [f.dict() for f in report_def.filters] if report_def.filters else []
                    }
                }
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to build custom report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report")


async def execute_report_query(session: Session, store_id: int, report_def: ReportDefinition) -> List[Dict[str, Any]]:
    """Execute the report query based on definition"""
    
    # Get base query for entity type
    if report_def.entity_type == "product":
        base_query = select(Product).where(Product.store_id == store_id)
        model = Product
    elif report_def.entity_type == "variant":
        base_query = select(ProductVariant).join(Product).where(Product.store_id == store_id)
        model = ProductVariant
    elif report_def.entity_type == "inventory":
        base_query = select(InventoryItem).where(InventoryItem.store_id == store_id)
        model = InventoryItem
    elif report_def.entity_type == "alert":
        base_query = select(Alert).where(Alert.store_id == store_id)
        model = Alert
    else:
        raise ValueError(f"Unknown entity type: {report_def.entity_type}")
    
    # Apply filters
    if report_def.filters:
        for filter_def in report_def.filters:
            base_query = apply_filter(base_query, model, filter_def)
    
    # Build aggregation query
    select_columns = []
    group_columns = []
    
    # Add group by columns
    for group_field in report_def.group_by or []:
        if group_field == GroupByType.DAY:
            select_columns.append(func.date_trunc('day', model.created_at).label('day'))
            group_columns.append('day')
        elif group_field == GroupByType.WEEK:
            select_columns.append(func.date_trunc('week', model.created_at).label('week'))
            group_columns.append('week')
        elif group_field == GroupByType.MONTH:
            select_columns.append(func.date_trunc('month', model.created_at).label('month'))
            group_columns.append('month')
        elif group_field == GroupByType.YEAR:
            select_columns.append(func.date_trunc('year', model.created_at).label('year'))
            group_columns.append('year')
        elif group_field == GroupByType.LOCATION and hasattr(model, 'location_id'):
            select_columns.append(model.location_id.label('location_id'))
            group_columns.append(model.location_id)
        elif group_field == GroupByType.PRODUCT_TYPE and hasattr(model, 'product_type'):
            select_columns.append(model.product_type.label('product_type'))
            group_columns.append(model.product_type)
        elif group_field == GroupByType.VENDOR and hasattr(model, 'vendor'):
            select_columns.append(model.vendor.label('vendor'))
            group_columns.append(model.vendor)
    
    # Add metric columns
    for metric in report_def.metrics:
        column = get_metric_column(model, metric)
        select_columns.append(column.label(metric.label or f"{metric.field}_{metric.aggregation}"))
    
    # Build final query
    if group_columns:
        final_query = select(*select_columns).select_from(base_query.subquery()).group_by(*group_columns)
    else:
        final_query = select(*select_columns).select_from(base_query.subquery())
    
    # Apply sorting
    if report_def.sort_by:
        sort_column = next((col for col in select_columns if col.key == report_def.sort_by), None)
        if sort_column is not None:
            if report_def.sort_order == "desc":
                final_query = final_query.order_by(desc(sort_column))
            else:
                final_query = final_query.order_by(sort_column)
    
    # Apply limit
    final_query = final_query.limit(report_def.limit)
    
    # Execute query
    result = await session.execute(final_query)
    rows = result.fetchall()
    
    # Convert to dict format
    report_data = []
    for row in rows:
        row_dict = {}
        for i, col in enumerate(select_columns):
            value = row[i]
            # Convert datetime to string
            if isinstance(value, datetime):
                value = value.isoformat()
            row_dict[col.key] = value
        report_data.append(row_dict)
    
    return report_data


def apply_filter(query, model, filter_def: ReportFilter):
    """Apply a filter to the query"""
    
    # Handle nested fields (e.g., custom_data.field_name)
    if '.' in filter_def.field:
        parts = filter_def.field.split('.')
        if parts[0] == 'custom_data' and hasattr(model, 'custom_data'):
            # JSONB field access
            field = model.custom_data[parts[1]]
        else:
            # Skip unknown nested fields
            return query
    else:
        if not hasattr(model, filter_def.field):
            return query
        field = getattr(model, filter_def.field)
    
    # Apply operator
    if filter_def.operator == "equals":
        query = query.where(field == filter_def.value)
    elif filter_def.operator == "not_equals":
        query = query.where(field != filter_def.value)
    elif filter_def.operator == "greater_than":
        query = query.where(field > filter_def.value)
    elif filter_def.operator == "less_than":
        query = query.where(field < filter_def.value)
    elif filter_def.operator == "contains":
        query = query.where(field.contains(str(filter_def.value)))
    elif filter_def.operator == "in":
        query = query.where(field.in_(filter_def.value))
    elif filter_def.operator == "between" and isinstance(filter_def.value, list) and len(filter_def.value) == 2:
        query = query.where(field.between(filter_def.value[0], filter_def.value[1]))
    
    return query


def get_metric_column(model, metric: ReportMetric):
    """Get the SQLAlchemy column for a metric"""
    
    # Handle nested fields
    if '.' in metric.field:
        parts = metric.field.split('.')
        if parts[0] == 'custom_data' and hasattr(model, 'custom_data'):
            # JSONB field access
            field = model.custom_data[parts[1]]
        else:
            # Default to count for unknown fields
            field = model.id
    else:
        field = getattr(model, metric.field, model.id)
    
    # Apply aggregation
    if metric.aggregation == AggregationType.SUM:
        return func.sum(field)
    elif metric.aggregation == AggregationType.AVG:
        return func.avg(field)
    elif metric.aggregation == AggregationType.COUNT:
        return func.count(field)
    elif metric.aggregation == AggregationType.MIN:
        return func.min(field)
    elif metric.aggregation == AggregationType.MAX:
        return func.max(field)
    elif metric.aggregation == AggregationType.COUNT_DISTINCT:
        return func.count(distinct(field))
    else:
        return func.count(field)


def create_csv_response(data: List[Dict[str, Any]], report_def: ReportDefinition):
    """Create a CSV response from report data"""
    
    output = io.StringIO()
    
    if data:
        # Get headers from first row
        headers = list(data[0].keys())
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={report_def.name.replace(' ', '_')}.csv"
        }
    )


# =============================================================================
# SAVED REPORTS ENDPOINTS
# =============================================================================

@router.get("/{shop_domain}/saved")
async def get_saved_reports(
    shop_domain: str,
    include_public: bool = Query(True)
):
    """Get saved report definitions"""
    
    # TODO: Implement saved reports storage
    # For now, return pre-built report templates
    
    templates = {
        "inventory_summary": {
            "name": "Inventory Summary by Location",
            "description": "Total inventory quantities and values by location",
            "definition": {
                "name": "Inventory Summary by Location",
                "entity_type": "inventory",
                "metrics": [
                    {"field": "available_quantity", "aggregation": "sum", "label": "Total Available"},
                    {"field": "on_hand_quantity", "aggregation": "sum", "label": "Total On Hand"},
                    {"field": "id", "aggregation": "count", "label": "SKU Count"}
                ],
                "group_by": ["location"],
                "sort_by": "Total Available",
                "sort_order": "desc"
            }
        },
        "low_stock_report": {
            "name": "Low Stock Report",
            "description": "Products below reorder point",
            "definition": {
                "name": "Low Stock Report",
                "entity_type": "inventory",
                "metrics": [
                    {"field": "available_quantity", "aggregation": "sum", "label": "Current Stock"},
                    {"field": "reorder_point", "aggregation": "avg", "label": "Reorder Point"}
                ],
                "filters": [
                    {"field": "available_quantity", "operator": "less_than", "value": 50}
                ],
                "sort_by": "Current Stock",
                "sort_order": "asc",
                "limit": 100
            }
        },
        "sales_by_category": {
            "name": "Sales by Product Type",
            "description": "Revenue breakdown by product category",
            "definition": {
                "name": "Sales by Product Type",
                "entity_type": "product",
                "metrics": [
                    {"field": "price", "aggregation": "sum", "label": "Total Revenue"},
                    {"field": "id", "aggregation": "count", "label": "Product Count"}
                ],
                "group_by": ["product_type"],
                "sort_by": "Total Revenue",
                "sort_order": "desc"
            }
        },
        "custom_field_analysis": {
            "name": "Custom Field Analysis",
            "description": "Analyze products by custom field values",
            "definition": {
                "name": "Custom Field Analysis",
                "entity_type": "product",
                "metrics": [
                    {"field": "id", "aggregation": "count", "label": "Product Count"},
                    {"field": "price", "aggregation": "avg", "label": "Avg Price"}
                ],
                "group_by": ["custom_field"],
                "sort_by": "Product Count",
                "sort_order": "desc"
            }
        },
        "alert_trends": {
            "name": "Alert Trends",
            "description": "Alert frequency and resolution metrics over time",
            "definition": {
                "name": "Alert Trends",
                "entity_type": "alert",
                "metrics": [
                    {"field": "id", "aggregation": "count", "label": "Total Alerts"},
                    {"field": "is_resolved", "aggregation": "sum", "label": "Resolved Count"}
                ],
                "group_by": ["month"],
                "sort_by": "month",
                "sort_order": "desc",
                "limit": 12
            }
        }
    }
    
    return {
        "saved_reports": list(templates.values()),
        "total_count": len(templates)
    }


# =============================================================================
# REPORT METRICS AND FIELDS
# =============================================================================

@router.get("/{shop_domain}/fields/{entity_type}")
async def get_available_fields(
    shop_domain: str,
    entity_type: str
):
    """Get available fields for reporting on an entity type"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop_domain)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Get standard fields for entity type
            standard_fields = get_standard_fields(entity_type)
            
            # Get custom fields
            result = await session.execute(
                select(CustomFieldDefinition).where(
                    and_(
                        CustomFieldDefinition.store_id == store.id,
                        CustomFieldDefinition.target_entity == entity_type,
                        CustomFieldDefinition.is_active == True
                    )
                )
            )
            custom_fields = result.scalars().all()
            
            # Format custom fields
            custom_field_list = []
            for cf in custom_fields:
                custom_field_list.append({
                    "field": f"custom_data.{cf.field_name}",
                    "label": cf.display_name,
                    "type": cf.field_type,
                    "category": "custom",
                    "aggregations": get_aggregations_for_type(cf.field_type)
                })
            
            return {
                "entity_type": entity_type,
                "standard_fields": standard_fields,
                "custom_fields": custom_field_list,
                "total_fields": len(standard_fields) + len(custom_field_list)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get available fields: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve fields")


def get_standard_fields(entity_type: str) -> List[Dict[str, Any]]:
    """Get standard fields for an entity type"""
    
    fields = {
        "product": [
            {"field": "id", "label": "Product ID", "type": "number", "category": "standard", "aggregations": ["count", "count_distinct"]},
            {"field": "title", "label": "Product Title", "type": "text", "category": "standard", "aggregations": ["count", "count_distinct"]},
            {"field": "product_type", "label": "Product Type", "type": "text", "category": "standard", "aggregations": ["count", "count_distinct"]},
            {"field": "vendor", "label": "Vendor", "type": "text", "category": "standard", "aggregations": ["count", "count_distinct"]},
            {"field": "price", "label": "Price", "type": "number", "category": "standard", "aggregations": ["sum", "avg", "min", "max"]},
            {"field": "cost_per_item", "label": "Cost", "type": "number", "category": "standard", "aggregations": ["sum", "avg", "min", "max"]},
            {"field": "created_at", "label": "Created Date", "type": "date", "category": "standard", "aggregations": ["min", "max"]}
        ],
        "variant": [
            {"field": "id", "label": "Variant ID", "type": "number", "category": "standard", "aggregations": ["count", "count_distinct"]},
            {"field": "sku", "label": "SKU", "type": "text", "category": "standard", "aggregations": ["count", "count_distinct"]},
            {"field": "title", "label": "Variant Title", "type": "text", "category": "standard", "aggregations": ["count", "count_distinct"]},
            {"field": "price", "label": "Price", "type": "number", "category": "standard", "aggregations": ["sum", "avg", "min", "max"]},
            {"field": "cost_per_item", "label": "Cost", "type": "number", "category": "standard", "aggregations": ["sum", "avg", "min", "max"]},
            {"field": "weight", "label": "Weight", "type": "number", "category": "standard", "aggregations": ["sum", "avg", "min", "max"]}
        ],
        "inventory": [
            {"field": "id", "label": "Inventory ID", "type": "number", "category": "standard", "aggregations": ["count", "count_distinct"]},
            {"field": "available_quantity", "label": "Available Qty", "type": "number", "category": "standard", "aggregations": ["sum", "avg", "min", "max"]},
            {"field": "on_hand_quantity", "label": "On Hand Qty", "type": "number", "category": "standard", "aggregations": ["sum", "avg", "min", "max"]},
            {"field": "committed_quantity", "label": "Committed Qty", "type": "number", "category": "standard", "aggregations": ["sum", "avg", "min", "max"]},
            {"field": "reorder_point", "label": "Reorder Point", "type": "number", "category": "standard", "aggregations": ["sum", "avg", "min", "max"]},
            {"field": "reorder_quantity", "label": "Reorder Qty", "type": "number", "category": "standard", "aggregations": ["sum", "avg", "min", "max"]},
            {"field": "lead_time_days", "label": "Lead Time", "type": "number", "category": "standard", "aggregations": ["avg", "min", "max"]}
        ],
        "alert": [
            {"field": "id", "label": "Alert ID", "type": "number", "category": "standard", "aggregations": ["count", "count_distinct"]},
            {"field": "alert_type", "label": "Alert Type", "type": "text", "category": "standard", "aggregations": ["count", "count_distinct"]},
            {"field": "severity", "label": "Severity", "type": "text", "category": "standard", "aggregations": ["count", "count_distinct"]},
            {"field": "is_resolved", "label": "Is Resolved", "type": "boolean", "category": "standard", "aggregations": ["sum", "count"]},
            {"field": "is_acknowledged", "label": "Is Acknowledged", "type": "boolean", "category": "standard", "aggregations": ["sum", "count"]},
            {"field": "created_at", "label": "Created Date", "type": "date", "category": "standard", "aggregations": ["min", "max"]}
        ]
    }
    
    return fields.get(entity_type, [])


def get_aggregations_for_type(field_type: str) -> List[str]:
    """Get available aggregations for a field type"""
    
    if field_type in ["number", "integer", "float"]:
        return ["sum", "avg", "min", "max", "count", "count_distinct"]
    elif field_type in ["text", "string", "select", "multi_select"]:
        return ["count", "count_distinct"]
    elif field_type in ["boolean"]:
        return ["sum", "count"]
    elif field_type in ["date", "datetime"]:
        return ["min", "max", "count", "count_distinct"]
    else:
        return ["count"]


# =============================================================================
# DASHBOARD WIDGETS
# =============================================================================

@router.get("/{shop_domain}/widgets")
async def get_dashboard_widgets(shop_domain: str):
    """Get pre-configured dashboard widgets"""
    
    widgets = [
        {
            "id": "total_inventory_value",
            "title": "Total Inventory Value",
            "type": "metric",
            "definition": {
                "entity_type": "inventory",
                "metrics": [
                    {"field": "available_quantity", "aggregation": "sum", "label": "value"}
                ]
            },
            "refresh_interval": 300  # 5 minutes
        },
        {
            "id": "low_stock_items",
            "title": "Low Stock Items",
            "type": "metric",
            "definition": {
                "entity_type": "inventory",
                "metrics": [
                    {"field": "id", "aggregation": "count", "label": "count"}
                ],
                "filters": [
                    {"field": "available_quantity", "operator": "less_than", "value": 10}
                ]
            },
            "refresh_interval": 300
        },
        {
            "id": "active_alerts",
            "title": "Active Alerts",
            "type": "metric",
            "definition": {
                "entity_type": "alert",
                "metrics": [
                    {"field": "id", "aggregation": "count", "label": "count"}
                ],
                "filters": [
                    {"field": "is_resolved", "operator": "equals", "value": False}
                ]
            },
            "refresh_interval": 60  # 1 minute
        },
        {
            "id": "inventory_by_location",
            "title": "Inventory by Location",
            "type": "chart",
            "chart_type": "bar",
            "definition": {
                "entity_type": "inventory",
                "metrics": [
                    {"field": "available_quantity", "aggregation": "sum", "label": "Quantity"}
                ],
                "group_by": ["location"]
            },
            "refresh_interval": 600  # 10 minutes
        }
    ]
    
    return {
        "widgets": widgets,
        "total_count": len(widgets)
    }