"""
Workflow Rules API - Advanced automation configuration
Create custom business logic and automation rules
"""

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, func
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
import json

from database import AsyncSessionLocal
from models import Store, WorkflowRule, WorkflowExecution
from workflow_engine import workflow_engine
from utils.logging import logger

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class WorkflowRuleCreate(BaseModel):
    rule_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    trigger_event: str = Field(..., pattern="^(inventory_low|custom_field_change|product_created|variant_low_stock|daily_schedule|manual)$")
    trigger_conditions: Dict[str, Any] = {}
    actions: List[Dict[str, Any]] = Field(..., min_items=1)
    priority: int = Field(default=100, ge=1, le=1000)
    max_executions_per_hour: int = Field(default=60, ge=0, le=3600)
    is_active: bool = True

    @validator('actions')
    def validate_actions(cls, v):
        """Validate action structure"""
        required_action_types = {
            "create_alert": ["message"],
            "update_field": ["entity_type", "field_name", "value"],
            "send_webhook": ["url"],
            "send_email": ["to_email", "subject", "message"]
        }
        
        for action in v:
            action_type = action.get("type")
            if not action_type:
                raise ValueError("Each action must have a 'type' field")
            
            if action_type in required_action_types:
                required_fields = required_action_types[action_type]
                for field in required_fields:
                    if field not in action:
                        raise ValueError(f"Action '{action_type}' missing required field: {field}")
        
        return v


class WorkflowRuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    description: Optional[str] = None
    trigger_conditions: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    priority: Optional[int] = None
    max_executions_per_hour: Optional[int] = None
    is_active: Optional[bool] = None


class ManualTriggerRequest(BaseModel):
    event_type: str
    event_data: Dict[str, Any] = {}


# =============================================================================
# WORKFLOW RULE ENDPOINTS
# =============================================================================

@router.get("/rules/{shop_domain}")
async def get_workflow_rules(
    shop_domain: str,
    is_active: Optional[bool] = Query(None),
    trigger_event: Optional[str] = Query(None),
    include_stats: bool = Query(True)
):
    """Get all workflow rules for a store"""
    
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
            query = select(WorkflowRule).where(WorkflowRule.store_id == store.id)
            
            if is_active is not None:
                query = query.where(WorkflowRule.is_active == is_active)
            
            if trigger_event:
                query = query.where(WorkflowRule.trigger_event == trigger_event)
            
            query = query.order_by(WorkflowRule.priority.asc(), WorkflowRule.created_at.desc())
            
            result = await session.execute(query)
            rules = result.scalars().all()
            
            # Format response
            rules_data = []
            for rule in rules:
                rule_data = {
                    "id": rule.id,
                    "rule_name": rule.rule_name,
                    "description": rule.description,
                    "trigger_event": rule.trigger_event,
                    "trigger_conditions": rule.trigger_conditions,
                    "actions": rule.actions,
                    "priority": rule.priority,
                    "max_executions_per_hour": rule.max_executions_per_hour,
                    "is_active": rule.is_active,
                    "execution_count": rule.execution_count,
                    "last_executed_at": rule.last_executed_at.isoformat() if rule.last_executed_at else None,
                    "created_at": rule.created_at.isoformat(),
                    "updated_at": rule.updated_at.isoformat()
                }
                
                # Add execution statistics if requested
                if include_stats:
                    stats = await get_rule_execution_stats(session, rule.id)
                    rule_data["stats"] = stats
                
                rules_data.append(rule_data)
            
            return {
                "rules": rules_data,
                "total_count": len(rules_data),
                "active_count": sum(1 for rule in rules if rule.is_active),
                "inactive_count": sum(1 for rule in rules if not rule.is_active)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow rules: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve workflow rules")


@router.post("/rules/{shop_domain}")
async def create_workflow_rule(
    shop_domain: str,
    rule: WorkflowRuleCreate
):
    """Create a new workflow rule"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop_domain)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Check plan limits
            result = await session.execute(
                select(WorkflowRule).where(
                    and_(
                        WorkflowRule.store_id == store.id,
                        WorkflowRule.is_active == True
                    )
                )
            )
            current_count = len(result.scalars().all())
            
            from shopify_billing import BillingPlanManager
            if not BillingPlanManager.check_feature_limit(store.subscription_plan, "workflows", current_count):
                plan_details = BillingPlanManager.get_plan_details(store.subscription_plan)
                limit = plan_details["limits"]["workflows"]
                raise HTTPException(
                    status_code=403,
                    detail=f"Plan limit reached. {store.subscription_plan.title()} plan allows {limit} active workflows."
                )
            
            # Create workflow rule
            new_rule = WorkflowRule(
                store_id=store.id,
                rule_name=rule.rule_name,
                description=rule.description,
                trigger_event=rule.trigger_event,
                trigger_conditions=rule.trigger_conditions,
                actions=rule.actions,
                priority=rule.priority,
                max_executions_per_hour=rule.max_executions_per_hour,
                is_active=rule.is_active
            )
            
            session.add(new_rule)
            await session.commit()
            await session.refresh(new_rule)
            
            logger.info(f"Created workflow rule for shop: {shop_domain}, rule_name: {rule.rule_name}, trigger_event: {rule.trigger_event}, actions_count: {len(rule.actions)}")
            
            return {
                "id": new_rule.id,
                "rule_name": new_rule.rule_name,
                "trigger_event": new_rule.trigger_event,
                "is_active": new_rule.is_active,
                "message": f"Workflow rule '{rule.rule_name}' created successfully"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create workflow rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to create workflow rule")


@router.put("/rules/{rule_id}")
async def update_workflow_rule(
    rule_id: int,
    shop_domain: str = Query(...),
    updates: WorkflowRuleUpdate = None
):
    """Update a workflow rule"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop_domain)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Get workflow rule
            result = await session.execute(
                select(WorkflowRule).where(
                    and_(
                        WorkflowRule.id == rule_id,
                        WorkflowRule.store_id == store.id
                    )
                )
            )
            rule = result.scalar_one_or_none()
            
            if not rule:
                raise HTTPException(status_code=404, detail="Workflow rule not found")
            
            # Update fields
            update_data = updates.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(rule, field, value)
            
            await session.commit()
            
            logger.info(f"Updated workflow rule for shop: {shop_domain}, rule_id: {rule_id}, rule_name: {rule.rule_name}")
            
            return {"message": f"Workflow rule '{rule.rule_name}' updated successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update workflow rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to update workflow rule")


@router.delete("/rules/{rule_id}")
async def delete_workflow_rule(
    rule_id: int,
    shop_domain: str = Query(...)
):
    """Delete a workflow rule"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop_domain)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Get workflow rule
            result = await session.execute(
                select(WorkflowRule).where(
                    and_(
                        WorkflowRule.id == rule_id,
                        WorkflowRule.store_id == store.id
                    )
                )
            )
            rule = result.scalar_one_or_none()
            
            if not rule:
                raise HTTPException(status_code=404, detail="Workflow rule not found")
            
            rule_name = rule.rule_name
            await session.delete(rule)
            await session.commit()
            
            logger.info(
                f"Deleted workflow rule",
                shop_domain=shop_domain,
                rule_id=rule_id,
                rule_name=rule_name
            )
            
            return {"message": f"Workflow rule '{rule_name}' deleted successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete workflow rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete workflow rule")


# =============================================================================
# EXECUTION AND TESTING ENDPOINTS
# =============================================================================

@router.post("/rules/{rule_id}/test")
async def test_workflow_rule(
    rule_id: int,
    shop_domain: str = Query(...),
    test_data: Dict[str, Any] = {}
):
    """Test a workflow rule with sample data"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop_domain)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Get workflow rule
            result = await session.execute(
                select(WorkflowRule).where(
                    and_(
                        WorkflowRule.id == rule_id,
                        WorkflowRule.store_id == store.id
                    )
                )
            )
            rule = result.scalar_one_or_none()
            
            if not rule:
                raise HTTPException(status_code=404, detail="Workflow rule not found")
            
            # Test the rule (without actually executing actions)
            from workflow_engine import WorkflowEngine
            engine = WorkflowEngine()
            
            # Evaluate conditions
            conditions_met = engine._evaluate_conditions(rule.trigger_conditions, test_data)
            
            return {
                "rule_name": rule.rule_name,
                "conditions_met": conditions_met,
                "test_data": test_data,
                "trigger_conditions": rule.trigger_conditions,
                "actions_count": len(rule.actions),
                "would_execute": conditions_met and rule.is_active
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test workflow rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to test workflow rule")


@router.post("/trigger/{shop_domain}")
async def trigger_manual_workflow(
    shop_domain: str,
    trigger_request: ManualTriggerRequest
):
    """Manually trigger workflow rules for testing"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop_domain)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Trigger the workflow
            await workflow_engine.trigger_event(
                store.id,
                trigger_request.event_type,
                trigger_request.event_data
            )
            
            logger.info(
                f"Manually triggered workflow",
                shop_domain=shop_domain,
                event_type=trigger_request.event_type
            )
            
            return {
                "message": f"Triggered {trigger_request.event_type} workflow",
                "event_data": trigger_request.event_data
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger workflow: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger workflow")


# =============================================================================
# EXECUTION HISTORY AND ANALYTICS
# =============================================================================

@router.get("/executions/{shop_domain}")
async def get_workflow_executions(
    shop_domain: str,
    rule_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None, pattern="^(success|failed|skipped)$"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get workflow execution history"""
    
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
            query = select(WorkflowExecution).join(WorkflowRule).where(
                WorkflowRule.store_id == store.id
            )
            
            if rule_id:
                query = query.where(WorkflowExecution.rule_id == rule_id)
            
            if status:
                query = query.where(WorkflowExecution.execution_status == status)
            
            query = query.order_by(WorkflowExecution.created_at.desc())
            query = query.offset(offset).limit(limit)
            
            result = await session.execute(query)
            executions = result.scalars().all()
            
            # Format response
            executions_data = []
            for execution in executions:
                executions_data.append({
                    "id": execution.id,
                    "rule_id": execution.rule_id,
                    "execution_status": execution.execution_status,
                    "error_message": execution.error_message,
                    "execution_time_ms": execution.execution_time_ms,
                    "trigger_data": execution.trigger_data,
                    "created_at": execution.created_at.isoformat()
                })
            
            return {
                "executions": executions_data,
                "total_count": len(executions_data),
                "offset": offset,
                "limit": limit
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow executions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve workflow executions")


@router.get("/analytics/{shop_domain}")
async def get_workflow_analytics(
    shop_domain: str,
    days: int = Query(30, ge=1, le=365)
):
    """Get workflow analytics and performance metrics"""
    
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
            
            # Get execution statistics
            result = await session.execute(
                select(
                    func.count(WorkflowExecution.id).label("total_executions"),
                    func.sum(func.case((WorkflowExecution.execution_status == "success", 1), else_=0)).label("successful_executions"),
                    func.sum(func.case((WorkflowExecution.execution_status == "failed", 1), else_=0)).label("failed_executions"),
                    func.avg(WorkflowExecution.execution_time_ms).label("avg_execution_time_ms")
                ).select_from(WorkflowExecution).join(WorkflowRule).where(
                    and_(
                        WorkflowRule.store_id == store.id,
                        WorkflowExecution.created_at >= start_date
                    )
                )
            )
            
            stats = result.first()
            
            # Get rule performance
            result = await session.execute(
                select(
                    WorkflowRule.rule_name,
                    WorkflowRule.trigger_event,
                    func.count(WorkflowExecution.id).label("execution_count"),
                    func.avg(WorkflowExecution.execution_time_ms).label("avg_time_ms")
                ).select_from(WorkflowRule).outerjoin(WorkflowExecution).where(
                    WorkflowRule.store_id == store.id
                ).group_by(WorkflowRule.id).order_by(desc("execution_count"))
            )
            
            rule_performance = [
                {
                    "rule_name": row.rule_name,
                    "trigger_event": row.trigger_event,
                    "execution_count": row.execution_count or 0,
                    "avg_execution_time_ms": float(row.avg_time_ms) if row.avg_time_ms else 0
                }
                for row in result
            ]
            
            return {
                "period_days": days,
                "summary": {
                    "total_executions": stats.total_executions or 0,
                    "successful_executions": stats.successful_executions or 0,
                    "failed_executions": stats.failed_executions or 0,
                    "success_rate": (stats.successful_executions or 0) / max(stats.total_executions or 1, 1) * 100,
                    "avg_execution_time_ms": float(stats.avg_execution_time_ms) if stats.avg_execution_time_ms else 0
                },
                "rule_performance": rule_performance
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve workflow analytics")


# =============================================================================
# WORKFLOW TEMPLATES
# =============================================================================

@router.get("/templates")
async def get_workflow_templates():
    """Get pre-built workflow templates"""
    
    templates = {
        "low_stock_alert": {
            "name": "Low Stock Alert",
            "description": "Send alert when inventory falls below reorder point",
            "trigger_event": "inventory_low",
            "trigger_conditions": {
                "type": "and",
                "conditions": [
                    {"field": "current_stock", "operator": "less_than_or_equal", "value": "{reorder_point}"},
                    {"field": "current_stock", "operator": "greater_than", "value": 0}
                ]
            },
            "actions": [
                {
                    "type": "create_alert",
                    "title": "Low Stock Alert",
                    "message": "Stock for {sku} is low. Current: {current_stock}, Reorder at: {reorder_point}",
                    "severity": "high",
                    "alert_type": "low_stock"
                }
            ]
        },
        "seasonal_product_automation": {
            "name": "Seasonal Product Automation",
            "description": "Automatically manage seasonal products",
            "trigger_event": "custom_field_change",
            "trigger_conditions": {
                "type": "and",
                "conditions": [
                    {"field": "field_name", "operator": "equals", "value": "season"},
                    {"field": "new_value", "operator": "equals", "value": "Winter"}
                ]
            },
            "actions": [
                {
                    "type": "update_field",
                    "entity_type": "product",
                    "field_name": "priority",
                    "value": "high"
                },
                {
                    "type": "create_alert",
                    "title": "Seasonal Product Updated",
                    "message": "Product {entity_id} marked as Winter seasonal item",
                    "severity": "info"
                }
            ]
        },
        "compliance_check": {
            "name": "Compliance Check",
            "description": "Ensure products meet compliance requirements",
            "trigger_event": "product_created",
            "trigger_conditions": {
                "type": "and",
                "conditions": [
                    {"field": "custom_data.category", "operator": "equals", "value": "food"},
                    {"field": "custom_data.expiry_date", "operator": "is_empty", "value": ""}
                ]
            },
            "actions": [
                {
                    "type": "create_alert",
                    "title": "Compliance Issue",
                    "message": "Food product {entity_id} missing expiry date",
                    "severity": "critical",
                    "alert_type": "compliance"
                }
            ]
        },
        "supplier_rating_update": {
            "name": "Supplier Rating Update",
            "description": "Update supplier rating based on delivery performance",
            "trigger_event": "custom_field_change",
            "trigger_conditions": {
                "type": "and",
                "conditions": [
                    {"field": "field_name", "operator": "equals", "value": "delivery_rating"},
                    {"field": "new_value", "operator": "less_than", "value": 3}
                ]
            },
            "actions": [
                {
                    "type": "create_alert",
                    "title": "Poor Supplier Performance",
                    "message": "Supplier rating dropped to {new_value}. Review required.",
                    "severity": "high"
                },
                {
                    "type": "send_webhook",
                    "url": "https://your-system.com/supplier-alerts",
                    "method": "POST"
                }
            ]
        }
    }
    
    return {"templates": templates}


async def get_rule_execution_stats(session: Session, rule_id: int) -> Dict[str, Any]:
    """Get execution statistics for a specific rule"""
    
    # Last 30 days stats
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    result = await session.execute(
        select(
            func.count(WorkflowExecution.id).label("total_executions"),
            func.sum(func.case((WorkflowExecution.execution_status == "success", 1), else_=0)).label("successful_executions"),
            func.sum(func.case((WorkflowExecution.execution_status == "failed", 1), else_=0)).label("failed_executions"),
            func.avg(WorkflowExecution.execution_time_ms).label("avg_execution_time_ms")
        ).where(
            and_(
                WorkflowExecution.rule_id == rule_id,
                WorkflowExecution.created_at >= thirty_days_ago
            )
        )
    )
    
    stats = result.first()
    
    return {
        "last_30_days": {
            "total_executions": stats.total_executions or 0,
            "successful_executions": stats.successful_executions or 0,
            "failed_executions": stats.failed_executions or 0,
            "success_rate": (stats.successful_executions or 0) / max(stats.total_executions or 1, 1) * 100,
            "avg_execution_time_ms": float(stats.avg_execution_time_ms) if stats.avg_execution_time_ms else 0
        }
    }