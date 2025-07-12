"""
Workflow Rules Engine - Advanced automation system
Executes custom business logic based on events and conditions
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session
import logging

from database import AsyncSessionLocal
from models import Store, WorkflowRule, WorkflowExecution, InventoryItem, Product, ProductVariant
from utils.logging import logger


class WorkflowEngine:
    """Main workflow execution engine"""
    
    def __init__(self):
        self.running = False
        self.execution_queue = asyncio.Queue()
    
    async def trigger_event(self, store_id: int, event_type: str, event_data: Dict[str, Any]):
        """Trigger workflow rules for a specific event"""
        
        try:
            async with AsyncSessionLocal() as session:
                # Get active rules for this event type
                result = await session.execute(
                    select(WorkflowRule).where(
                        and_(
                            WorkflowRule.store_id == store_id,
                            WorkflowRule.trigger_event == event_type,
                            WorkflowRule.is_active == True
                        )
                    ).order_by(WorkflowRule.priority.asc())
                )
                
                rules = result.scalars().all()
                
                logger.info(
                    f"Triggered workflow event",
                    store_id=store_id,
                    event_type=event_type,
                    rules_found=len(rules)
                )
                
                # Execute each rule
                for rule in rules:
                    await self._execute_rule(rule, event_data, session)
                    
        except Exception as e:
            logger.error(f"Failed to trigger workflow event: {e}", exc_info=e)
    
    async def _execute_rule(self, rule: WorkflowRule, event_data: Dict[str, Any], session: Session):
        """Execute a single workflow rule"""
        
        start_time = time.time()
        execution_status = "success"
        error_message = None
        
        try:
            # Check rate limiting
            if not await self._check_rate_limit(rule, session):
                logger.info(f"Rule rate limited: {rule.rule_name}")
                return
            
            # Evaluate conditions
            if not self._evaluate_conditions(rule.trigger_conditions, event_data):
                logger.debug(f"Rule conditions not met: {rule.rule_name}")
                return
            
            # Execute actions
            await self._execute_actions(rule.actions, event_data, rule.store_id, session)
            
            # Update rule execution count
            rule.execution_count += 1
            rule.last_executed_at = datetime.now()
            
            logger.info(
                f"Executed workflow rule",
                rule_id=rule.id,
                rule_name=rule.rule_name,
                execution_count=rule.execution_count
            )
            
        except Exception as e:
            execution_status = "failed"
            error_message = str(e)
            logger.error(f"Rule execution failed: {rule.rule_name} - {e}")
        
        finally:
            # Log execution
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            execution_log = WorkflowExecution(
                rule_id=rule.id,
                trigger_data=event_data,
                execution_status=execution_status,
                error_message=error_message,
                execution_time_ms=execution_time_ms
            )
            
            session.add(execution_log)
            await session.commit()
    
    async def _check_rate_limit(self, rule: WorkflowRule, session: Session) -> bool:
        """Check if rule execution is within rate limits"""
        
        if rule.max_executions_per_hour <= 0:
            return True
        
        # Count executions in the last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        
        result = await session.execute(
            select(WorkflowExecution).where(
                and_(
                    WorkflowExecution.rule_id == rule.id,
                    WorkflowExecution.created_at >= one_hour_ago
                )
            )
        )
        
        recent_executions = len(result.scalars().all())
        return recent_executions < rule.max_executions_per_hour
    
    def _evaluate_conditions(self, conditions: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        """Evaluate rule conditions against event data"""
        
        if not conditions:
            return True
        
        # Handle different condition types
        condition_type = conditions.get("type", "and")
        
        if condition_type == "and":
            return self._evaluate_and_conditions(conditions.get("conditions", []), event_data)
        elif condition_type == "or":
            return self._evaluate_or_conditions(conditions.get("conditions", []), event_data)
        else:
            return self._evaluate_single_condition(conditions, event_data)
    
    def _evaluate_and_conditions(self, conditions: List[Dict], event_data: Dict[str, Any]) -> bool:
        """All conditions must be true"""
        return all(self._evaluate_single_condition(cond, event_data) for cond in conditions)
    
    def _evaluate_or_conditions(self, conditions: List[Dict], event_data: Dict[str, Any]) -> bool:
        """At least one condition must be true"""
        return any(self._evaluate_single_condition(cond, event_data) for cond in conditions)
    
    def _evaluate_single_condition(self, condition: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        """Evaluate a single condition"""
        
        field_path = condition.get("field")
        operator = condition.get("operator")
        expected_value = condition.get("value")
        
        if not field_path or not operator:
            return False
        
        # Get actual value from event data
        actual_value = self._get_nested_value(event_data, field_path)
        
        # Evaluate based on operator
        return self._apply_operator(actual_value, operator, expected_value)
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get value from nested dict using dot notation"""
        
        keys = path.split(".")
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _apply_operator(self, actual: Any, operator: str, expected: Any) -> bool:
        """Apply comparison operator"""
        
        try:
            if operator == "equals":
                return actual == expected
            elif operator == "not_equals":
                return actual != expected
            elif operator == "greater_than":
                return float(actual) > float(expected)
            elif operator == "less_than":
                return float(actual) < float(expected)
            elif operator == "greater_than_or_equal":
                return float(actual) >= float(expected)
            elif operator == "less_than_or_equal":
                return float(actual) <= float(expected)
            elif operator == "contains":
                return str(expected).lower() in str(actual).lower()
            elif operator == "not_contains":
                return str(expected).lower() not in str(actual).lower()
            elif operator == "starts_with":
                return str(actual).lower().startswith(str(expected).lower())
            elif operator == "ends_with":
                return str(actual).lower().endswith(str(expected).lower())
            elif operator == "in":
                return actual in expected if isinstance(expected, list) else False
            elif operator == "not_in":
                return actual not in expected if isinstance(expected, list) else True
            elif operator == "is_empty":
                return actual is None or actual == "" or actual == []
            elif operator == "is_not_empty":
                return actual is not None and actual != "" and actual != []
            else:
                logger.warning(f"Unknown operator: {operator}")
                return False
        except (ValueError, TypeError) as e:
            logger.warning(f"Condition evaluation error: {e}")
            return False
    
    async def _execute_actions(self, actions: List[Dict[str, Any]], event_data: Dict[str, Any], store_id: int, session: Session):
        """Execute all actions for a rule"""
        
        for action in actions:
            await self._execute_single_action(action, event_data, store_id, session)
    
    async def _execute_single_action(self, action: Dict[str, Any], event_data: Dict[str, Any], store_id: int, session: Session):
        """Execute a single action"""
        
        action_type = action.get("type")
        
        try:
            if action_type == "create_alert":
                await self._action_create_alert(action, event_data, store_id, session)
            elif action_type == "update_field":
                await self._action_update_field(action, event_data, store_id, session)
            elif action_type == "send_webhook":
                await self._action_send_webhook(action, event_data, store_id)
            elif action_type == "send_email":
                await self._action_send_email(action, event_data, store_id)
            elif action_type == "create_purchase_order":
                await self._action_create_purchase_order(action, event_data, store_id, session)
            else:
                logger.warning(f"Unknown action type: {action_type}")
        
        except Exception as e:
            logger.error(f"Action execution failed: {action_type} - {e}")
    
    async def _action_create_alert(self, action: Dict[str, Any], event_data: Dict[str, Any], store_id: int, session: Session):
        """Create an alert"""
        
        from models import Alert
        
        # Template the message with event data
        message = self._template_string(action.get("message", "Workflow alert triggered"), event_data)
        title = self._template_string(action.get("title", "Workflow Alert"), event_data)
        
        alert = Alert(
            store_id=store_id,
            alert_type=action.get("alert_type", "workflow"),
            severity=action.get("severity", "medium"),
            title=title,
            message=message,
            product_sku=event_data.get("sku"),
            location_name=event_data.get("location_name"),
            current_stock=event_data.get("current_stock"),
            recommended_action=action.get("recommended_action")
        )
        
        session.add(alert)
        logger.info(f"Created workflow alert: {title}")
    
    async def _action_update_field(self, action: Dict[str, Any], event_data: Dict[str, Any], store_id: int, session: Session):
        """Update a custom field on an entity"""
        
        entity_type = action.get("entity_type")
        entity_id = event_data.get("entity_id")
        field_name = action.get("field_name")
        new_value = self._template_string(str(action.get("value", "")), event_data)
        
        if not all([entity_type, entity_id, field_name]):
            logger.warning("Missing required parameters for update_field action")
            return
        
        # Get entity model
        entity_model = {
            "product": Product,
            "variant": ProductVariant,
            "inventory_item": InventoryItem
        }.get(entity_type)
        
        if not entity_model:
            logger.warning(f"Unknown entity type: {entity_type}")
            return
        
        # Update entity
        result = await session.execute(
            select(entity_model).where(entity_model.id == entity_id)
        )
        entity = result.scalar_one_or_none()
        
        if entity:
            custom_data = entity.custom_data or {}
            custom_data[field_name] = new_value
            entity.custom_data = custom_data
            
            logger.info(f"Updated {entity_type} {entity_id} field {field_name} to {new_value}")
    
    async def _action_send_webhook(self, action: Dict[str, Any], event_data: Dict[str, Any], store_id: int):
        """Send a webhook"""
        
        import httpx
        
        url = action.get("url")
        if not url:
            logger.warning("No URL provided for webhook action")
            return
        
        # Prepare payload
        payload = {
            "event": "workflow_triggered",
            "store_id": store_id,
            "timestamp": datetime.now().isoformat(),
            "data": event_data,
            "action": action
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    timeout=30.0,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    logger.info(f"Webhook sent successfully to {url}")
                else:
                    logger.warning(f"Webhook failed: {url} returned {response.status_code}")
        
        except Exception as e:
            logger.error(f"Webhook error: {e}")
    
    async def _action_send_email(self, action: Dict[str, Any], event_data: Dict[str, Any], store_id: int):
        """Send an email notification"""
        
        # TODO: Implement email sending
        # This would integrate with email service (SendGrid, AWS SES, etc.)
        
        to_email = action.get("to_email")
        subject = self._template_string(action.get("subject", "Workflow Notification"), event_data)
        message = self._template_string(action.get("message", ""), event_data)
        
        logger.info(f"Email notification (not implemented): {to_email} - {subject}")
    
    async def _action_create_purchase_order(self, action: Dict[str, Any], event_data: Dict[str, Any], store_id: int, session: Session):
        """Automatically create a purchase order"""
        
        # TODO: Implement automatic PO creation
        # This would create PO based on reorder rules
        
        logger.info("Purchase order creation (not implemented)")
    
    def _template_string(self, template: str, data: Dict[str, Any]) -> str:
        """Replace template variables with actual values"""
        
        result = template
        
        for key, value in data.items():
            placeholder = f"{{{key}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        
        return result


# Global workflow engine instance
workflow_engine = WorkflowEngine()


# Convenience functions for triggering common events
async def trigger_inventory_low(store_id: int, inventory_item_id: int, current_stock: int, reorder_point: int):
    """Trigger inventory low event"""
    
    event_data = {
        "entity_type": "inventory_item",
        "entity_id": inventory_item_id,
        "current_stock": current_stock,
        "reorder_point": reorder_point,
        "stock_ratio": current_stock / reorder_point if reorder_point > 0 else 0
    }
    
    await workflow_engine.trigger_event(store_id, "inventory_low", event_data)


async def trigger_custom_field_change(store_id: int, entity_type: str, entity_id: int, field_name: str, old_value: Any, new_value: Any):
    """Trigger custom field change event"""
    
    event_data = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "field_name": field_name,
        "old_value": old_value,
        "new_value": new_value
    }
    
    await workflow_engine.trigger_event(store_id, "custom_field_change", event_data)


async def trigger_product_created(store_id: int, product_id: int, product_data: Dict[str, Any]):
    """Trigger product created event"""
    
    event_data = {
        "entity_type": "product",
        "entity_id": product_id,
        **product_data
    }
    
    await workflow_engine.trigger_event(store_id, "product_created", event_data)


async def trigger_variant_low_stock(store_id: int, variant_id: int, sku: str, current_stock: int, location_name: str):
    """Trigger variant low stock event"""
    
    event_data = {
        "entity_type": "variant",
        "entity_id": variant_id,
        "sku": sku,
        "current_stock": current_stock,
        "location_name": location_name
    }
    
    await workflow_engine.trigger_event(store_id, "variant_low_stock", event_data)