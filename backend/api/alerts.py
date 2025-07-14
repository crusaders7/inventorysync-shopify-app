"""
Enhanced Alerts API - Smart alerting with custom templates
Advanced notification system with custom conditions and actions
"""

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, desc, func
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
import json

from database import AsyncSessionLocal
from models import Store, Alert, AlertTemplate
from utils.logging import logger

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class AlertCreate(BaseModel):
    alert_type: str = Field(..., pattern="^(low_stock|overstock|reorder|compliance|workflow|custom|manual)$")
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=2000)
    product_sku: Optional[str] = None
    location_name: Optional[str] = None
    current_stock: Optional[int] = None
    recommended_action: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    custom_data: Dict[str, Any] = {}
    notification_channels: List[str] = []
    auto_resolve_hours: Optional[int] = None


class AlertUpdate(BaseModel):
    is_acknowledged: Optional[bool] = None
    is_resolved: Optional[bool] = None
    resolution_notes: Optional[str] = None
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None


class AlertTemplateCreate(BaseModel):
    template_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    alert_type: str = Field(..., pattern="^(low_stock|overstock|reorder|compliance|workflow|custom)$")
    title_template: str = Field(..., min_length=1, max_length=200)
    message_template: str = Field(..., min_length=1, max_length=2000)
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    trigger_conditions: Dict[str, Any] = {}
    notification_channels: List[str] = []
    notification_config: Dict[str, Any] = {}
    auto_resolve_hours: Optional[int] = None


class AlertTemplateUpdate(BaseModel):
    template_name: Optional[str] = None
    description: Optional[str] = None
    title_template: Optional[str] = None
    message_template: Optional[str] = None
    severity: Optional[str] = None
    trigger_conditions: Optional[Dict[str, Any]] = None
    notification_channels: Optional[List[str]] = None
    notification_config: Optional[Dict[str, Any]] = None
    auto_resolve_hours: Optional[int] = None
    is_active: Optional[bool] = None


# =============================================================================
# ALERT ENDPOINTS
# =============================================================================

@router.get("/{shop_domain}")
async def get_alerts(
    shop_domain: str,
    status: Optional[str] = Query(None, pattern="^(active|acknowledged|resolved|all)$"),
    severity: Optional[str] = Query(None, pattern="^(low|medium|high|critical)$"),
    alert_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at", pattern="^(created_at|severity|alert_type|title)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$")
):
    """Get alerts for a store with filtering and sorting"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop_domain)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Build query
            query = select(Alert).where(Alert.store_id == store.id)
            
            # Apply filters
            if status and status != "all":
                if status == "active":
                    query = query.where(and_(Alert.is_acknowledged == False, Alert.is_resolved == False))
                elif status == "acknowledged":
                    query = query.where(and_(Alert.is_acknowledged == True, Alert.is_resolved == False))
                elif status == "resolved":
                    query = query.where(Alert.is_resolved == True)
            
            if severity:
                query = query.where(Alert.severity == severity)
            
            if alert_type:
                query = query.where(Alert.alert_type == alert_type)
            
            # Apply sorting
            if sort_by == "created_at":
                sort_column = Alert.created_at
            elif sort_by == "severity":
                # Custom severity ordering: critical > high > medium > low
                severity_order = {
                    "critical": 4,
                    "high": 3,
                    "medium": 2,
                    "low": 1
                }
                sort_column = Alert.severity
            else:
                sort_column = getattr(Alert, sort_by)
            
            if sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(sort_column)
            
            # Apply pagination
            query = query.offset(offset).limit(limit)
            
            result = await session.execute(query)
            alerts = result.scalars().all()
            
            # Get total count
            count_query = select(func.count(Alert.id)).where(Alert.store_id == store.id)
            if status and status != "all":
                if status == "active":
                    count_query = count_query.where(and_(Alert.is_acknowledged == False, Alert.is_resolved == False))
                elif status == "acknowledged":
                    count_query = count_query.where(and_(Alert.is_acknowledged == True, Alert.is_resolved == False))
                elif status == "resolved":
                    count_query = count_query.where(Alert.is_resolved == True)
            
            result = await session.execute(count_query)
            total_count = result.scalar()
            
            # Format response
            alerts_data = []
            for alert in alerts:
                alerts_data.append({
                    "id": alert.id,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "title": alert.title,
                    "message": alert.message,
                    "product_sku": alert.product_sku,
                    "location_name": alert.location_name,
                    "current_stock": alert.current_stock,
                    "recommended_action": alert.recommended_action,
                    "alert_source": alert.alert_source,
                    "entity_type": alert.entity_type,
                    "entity_id": alert.entity_id,
                    "custom_data": alert.custom_data,
                    "notification_channels": alert.notification_channels,
                    "is_acknowledged": alert.is_acknowledged,
                    "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                    "acknowledged_by": alert.acknowledged_by,
                    "is_resolved": alert.is_resolved,
                    "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                    "resolved_by": alert.resolved_by,
                    "resolution_notes": alert.resolution_notes,
                    "auto_resolve_at": alert.auto_resolve_at.isoformat() if alert.auto_resolve_at else None,
                    "created_at": alert.created_at.isoformat(),
                    "updated_at": alert.updated_at.isoformat()
                })
            
            return {
                "alerts": alerts_data,
                "total_count": total_count,
                "offset": offset,
                "limit": limit,
                "has_more": offset + len(alerts_data) < total_count
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


@router.post("/{shop_domain}")
async def create_alert(
    shop_domain: str,
    alert: AlertCreate
):
    """Create a new alert"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop_domain)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Create alert
            new_alert = Alert(
                store_id=store.id,
                alert_type=alert.alert_type,
                severity=alert.severity,
                title=alert.title,
                message=alert.message,
                product_sku=alert.product_sku,
                location_name=alert.location_name,
                current_stock=alert.current_stock,
                recommended_action=alert.recommended_action,
                alert_source="manual",
                entity_type=alert.entity_type,
                entity_id=alert.entity_id,
                custom_data=alert.custom_data,
                notification_channels=alert.notification_channels
            )
            
            # Set auto-resolve
            if alert.auto_resolve_hours:
                new_alert.auto_resolve_at = datetime.now() + timedelta(hours=alert.auto_resolve_hours)
                new_alert.is_auto_resolvable = True
            
            session.add(new_alert)
            await session.commit()
            await session.refresh(new_alert)
            
            logger.info(
                f"Created alert",
                shop_domain=shop_domain,
                alert_type=alert.alert_type,
                severity=alert.severity,
                title=alert.title
            )
            
            return {
                "id": new_alert.id,
                "alert_type": new_alert.alert_type,
                "severity": new_alert.severity,
                "title": new_alert.title,
                "message": f"Alert '{alert.title}' created successfully"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to create alert")


@router.put("/{alert_id}")
async def update_alert(
    alert_id: int,
    shop_domain: str = Query(...),
    updates: AlertUpdate = None
):
    """Update an alert (acknowledge, resolve, etc.)"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop_domain)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Get alert
            result = await session.execute(
                select(Alert).where(
                    and_(
                        Alert.id == alert_id,
                        Alert.store_id == store.id
                    )
                )
            )
            alert = result.scalar_one_or_none()
            
            if not alert:
                raise HTTPException(status_code=404, detail="Alert not found")
            
            # Update fields
            update_data = updates.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                if field == "is_acknowledged" and value and not alert.is_acknowledged:
                    alert.acknowledged_at = datetime.now()
                elif field == "is_resolved" and value and not alert.is_resolved:
                    alert.resolved_at = datetime.now()
                
                setattr(alert, field, value)
            
            await session.commit()
            
            action = "acknowledged" if updates.is_acknowledged else "resolved" if updates.is_resolved else "updated"
            
            logger.info(
                f"Alert {action}",
                shop_domain=shop_domain,
                alert_id=alert_id,
                title=alert.title
            )
            
            return {"message": f"Alert '{alert.title}' {action} successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to update alert")


@router.get("/analytics/{shop_domain}")
async def get_alert_analytics(
    shop_domain: str,
    days: int = Query(30, ge=1, le=365)
):
    """Get alert analytics and metrics"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop_domain)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get alert statistics
            result = await session.execute(
                select(
                    func.count(Alert.id).label("total_alerts"),
                    func.sum(func.case((Alert.is_resolved == True, 1), else_=0)).label("resolved_alerts"),
                    func.sum(func.case((Alert.is_acknowledged == True, 1), else_=0)).label("acknowledged_alerts"),
                    func.sum(func.case((and_(Alert.is_acknowledged == False, Alert.is_resolved == False), 1), else_=0)).label("active_alerts")
                ).where(
                    and_(
                        Alert.store_id == store.id,
                        Alert.created_at >= start_date
                    )
                )
            )
            
            stats = result.first()
            
            # Get alerts by type
            result = await session.execute(
                select(
                    Alert.alert_type,
                    func.count(Alert.id).label("count")
                ).where(
                    and_(
                        Alert.store_id == store.id,
                        Alert.created_at >= start_date
                    )
                ).group_by(Alert.alert_type).order_by(desc("count"))
            )
            
            alerts_by_type = [
                {"alert_type": row.alert_type, "count": row.count}
                for row in result
            ]
            
            # Get alerts by severity
            result = await session.execute(
                select(
                    Alert.severity,
                    func.count(Alert.id).label("count")
                ).where(
                    and_(
                        Alert.store_id == store.id,
                        Alert.created_at >= start_date
                    )
                ).group_by(Alert.severity).order_by(desc("count"))
            )
            
            alerts_by_severity = [
                {"severity": row.severity, "count": row.count}
                for row in result
            ]
            
            return {
                "period_days": days,
                "summary": {
                    "total_alerts": stats.total_alerts or 0,
                    "resolved_alerts": stats.resolved_alerts or 0,
                    "acknowledged_alerts": stats.acknowledged_alerts or 0,
                    "active_alerts": stats.active_alerts or 0,
                    "resolution_rate": (stats.resolved_alerts or 0) / max(stats.total_alerts or 1, 1) * 100
                },
                "breakdown": {
                    "by_type": alerts_by_type,
                    "by_severity": alerts_by_severity
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alert analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alert analytics")


# Legacy endpoints for compatibility
@router.get("/")
async def get_alerts_legacy():
    """Legacy alerts endpoint - redirects to main endpoint"""
    return {"message": "Please use /api/v1/alerts/{shop_domain} instead"}


@router.get("/summary")
async def get_alerts_summary():
    """Legacy summary endpoint"""
    return {"message": "Please use /api/v1/alerts/analytics/{shop_domain} instead"}