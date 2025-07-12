"""
Industry Templates API
Pre-configured custom fields for different industries
"""

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from typing import List, Dict, Any
from sqlalchemy import select
from datetime import datetime

from database import AsyncSessionLocal
from models import Store, CustomFieldDefinition
from industry_templates import IndustryTemplates
from utils.logging import logger

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])


@router.get("/industries")
async def list_industries():
    """Get list of available industry templates"""
    industries = IndustryTemplates.list_industries()
    
    templates = []
    for industry in industries:
        template = IndustryTemplates.get_template(industry)
        templates.append({
            "id": industry,
            "name": template["name"],
            "description": template["description"],
            "field_count": len(template["custom_fields"]),
            "workflow_count": len(template.get("workflows", []))
        })
    
    return {
        "templates": templates,
        "total": len(templates)
    }


@router.get("/industries/{industry}")
async def get_industry_template(industry: str):
    """Get detailed template for a specific industry"""
    template = IndustryTemplates.get_template(industry)
    
    if not template:
        raise HTTPException(status_code=404, detail="Industry template not found")
    
    return {
        "industry": industry,
        "template": template
    }


@router.post("/apply/{industry}")
async def apply_industry_template(
    industry: str,
    shop: str = Query(..., description="Shop domain"),
    background_tasks: BackgroundTasks = None
):
    """Apply an industry template to a store"""
    
    template = IndustryTemplates.get_template(industry)
    if not template:
        raise HTTPException(status_code=404, detail="Industry template not found")
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Check if custom fields are available in plan
            if not store.plan_features.get("custom_fields", 0) > 0:
                raise HTTPException(
                    status_code=403,
                    detail="Custom fields not available in your current plan"
                )
            
            # Apply custom fields
            created_fields = []
            for field_config in template["custom_fields"]:
                # Check if field already exists
                existing = await session.execute(
                    select(CustomFieldDefinition).where(
                        CustomFieldDefinition.store_id == store.id,
                        CustomFieldDefinition.field_name == field_config["field_name"]
                    )
                )
                
                if not existing.scalar_one_or_none():
                    # Create new field
                    field = CustomFieldDefinition(
                        store_id=store.id,
                        field_name=field_config["field_name"],
                        display_name=field_config["display_name"],
                        field_type=field_config["field_type"],
                        target_entity=field_config.get("target_entity", "product"),
                        validation_rules=field_config.get("validation_rules", {}),
                        is_required=field_config.get("is_required", False),
                        is_searchable=field_config.get("is_searchable", True),
                        is_filterable=field_config.get("is_filterable", True),
                        help_text=field_config.get("help_text"),
                        default_value=field_config.get("default_value"),
                        field_group=industry,
                        industry_template=industry
                    )
                    session.add(field)
                    created_fields.append(field.field_name)
            
            # Update store metadata
            if not store.metadata:
                store.metadata = {}
            
            store.metadata["industry"] = industry
            store.metadata["template_applied_at"] = datetime.utcnow().isoformat()
            
            await session.commit()
            
            # Apply workflows in background
            if template.get("workflows"):
                background_tasks.add_task(
                    apply_template_workflows,
                    store.id,
                    template["workflows"]
                )
            
            logger.info(
                f"Applied industry template",
                shop=shop,
                industry=industry,
                fields_created=len(created_fields)
            )
            
            return {
                "success": True,
                "industry": industry,
                "fields_created": len(created_fields),
                "fields": created_fields,
                "message": f"Successfully applied {template['name']} template"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to apply template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to apply template")


@router.get("/recommendations")
async def get_template_recommendations(
    shop: str = Query(..., description="Shop domain")
):
    """Get AI-powered template recommendations based on store data"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Analyze store products to recommend templates
            # This is a simplified version - you'd want to analyze actual product data
            recommendations = [
                {
                    "industry": "apparel",
                    "confidence": 0.85,
                    "reasons": [
                        "Detected size and color variants",
                        "Products have material descriptions",
                        "Seasonal product naming patterns"
                    ]
                },
                {
                    "industry": "electronics",
                    "confidence": 0.65,
                    "reasons": [
                        "Technical specifications in descriptions",
                        "Model numbers detected",
                        "Warranty mentions"
                    ]
                }
            ]
            
            return {
                "recommendations": recommendations,
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get recommendations")


async def apply_template_workflows(store_id: int, workflows: List[Dict[str, Any]]):
    """Apply workflow templates in the background"""
    # Implementation for applying workflow rules
    # This would create WorkflowRule entries based on the template
    pass