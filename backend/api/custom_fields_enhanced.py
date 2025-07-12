"""
Enhanced Custom Fields API with advanced features
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from pydantic import BaseModel, validator

from database import get_db
from models import CustomFieldDefinition, Store
# from simple_auth import get_current_store as get_current_user, check_rate_limit
# from utils.cache import cache_result
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/custom-fields",
    tags=["custom-fields-enhanced"],
    # dependencies=[Depends(get_current_user), Depends(check_rate_limit)]
)

# Enhanced Models
class ValidationRule(BaseModel):
    required: bool = False
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    allowed_values: Optional[List[str]] = None

class CustomFieldCreate(BaseModel):
    name: str
    field_type: str
    label: str
    description: Optional[str] = None
    default_value: Optional[Any] = None
    options: Optional[List[str]] = None
    validation_rules: Optional[ValidationRule] = None
    is_active: bool = True
    show_in_list: bool = True
    searchable: bool = True
    sortable: bool = True
    
    @validator('field_type')
    def validate_field_type(cls, v):
        allowed_types = ['text', 'number', 'select', 'boolean', 'date', 'email', 'url', 'multiselect', 'textarea', 'json']
        if v not in allowed_types:
            raise ValueError(f'Field type must be one of {allowed_types}')
        return v

class BulkOperation(BaseModel):
    operation: str  # 'create', 'update', 'delete'
    field_ids: Optional[List[int]] = None
    field_data: Optional[List[CustomFieldCreate]] = None
    update_data: Optional[Dict[str, Any]] = None

class FieldTemplate(BaseModel):
    name: str
    description: str
    fields: List[CustomFieldCreate]
    category: str

# Field Templates
FIELD_TEMPLATES = {
    "clothing": FieldTemplate(
        name="Clothing & Apparel",
        description="Common fields for clothing and fashion items",
        category="retail",
        fields=[
            CustomFieldCreate(
                name="size",
                field_type="select",
                label="Size",
                options=["XS", "S", "M", "L", "XL", "XXL"],
                validation_rules=ValidationRule(required=True)
            ),
            CustomFieldCreate(
                name="color",
                field_type="text",
                label="Color",
                validation_rules=ValidationRule(required=True)
            ),
            CustomFieldCreate(
                name="material",
                field_type="text",
                label="Material",
                description="Primary material composition"
            ),
            CustomFieldCreate(
                name="care_instructions",
                field_type="textarea",
                label="Care Instructions"
            ),
            CustomFieldCreate(
                name="season",
                field_type="multiselect",
                label="Season",
                options=["Spring", "Summer", "Fall", "Winter"]
            )
        ]
    ),
    "electronics": FieldTemplate(
        name="Electronics",
        description="Fields for electronic products",
        category="technology",
        fields=[
            CustomFieldCreate(
                name="warranty_period",
                field_type="number",
                label="Warranty Period (months)",
                validation_rules=ValidationRule(min_value=0, max_value=60)
            ),
            CustomFieldCreate(
                name="voltage",
                field_type="select",
                label="Voltage",
                options=["110V", "220V", "Universal"],
                validation_rules=ValidationRule(required=True)
            ),
            CustomFieldCreate(
                name="power_consumption",
                field_type="number",
                label="Power Consumption (W)"
            ),
            CustomFieldCreate(
                name="connectivity",
                field_type="multiselect",
                label="Connectivity",
                options=["WiFi", "Bluetooth", "USB", "Ethernet", "HDMI"]
            )
        ]
    ),
    "food_beverage": FieldTemplate(
        name="Food & Beverage",
        description="Fields for food and beverage products",
        category="consumables",
        fields=[
            CustomFieldCreate(
                name="expiry_date",
                field_type="date",
                label="Expiry Date",
                validation_rules=ValidationRule(required=True)
            ),
            CustomFieldCreate(
                name="ingredients",
                field_type="textarea",
                label="Ingredients List"
            ),
            CustomFieldCreate(
                name="allergens",
                field_type="multiselect",
                label="Allergens",
                options=["Gluten", "Dairy", "Nuts", "Soy", "Eggs", "Shellfish"]
            ),
            CustomFieldCreate(
                name="storage_temperature",
                field_type="select",
                label="Storage Temperature",
                options=["Room Temperature", "Refrigerated", "Frozen"]
            )
        ]
    )
}

@router.get("/templates")
# @cache_result(expire=3600)
async def get_field_templates():
    """Get available field templates"""
    return {
        "templates": [
            {
                "id": key,
                "name": template.name,
                "description": template.description,
                "category": template.category,
                "field_count": len(template.fields)
            }
            for key, template in FIELD_TEMPLATES.items()
        ]
    }

@router.get("/templates/{template_id}")
async def get_template_details(template_id: str):
    """Get detailed template with all fields"""
    if template_id not in FIELD_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template = FIELD_TEMPLATES[template_id]
    return {
        "id": template_id,
        "name": template.name,
        "description": template.description,
        "category": template.category,
        "fields": [field.dict() for field in template.fields]
    }

@router.post("/templates/{template_id}/apply/{shop_domain}")
async def apply_template(
    template_id: str,
    shop_domain: str,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Apply a template to create multiple fields at once"""
    if template_id not in FIELD_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    
    store = db.query(Store).filter(Store.shopify_domain == shop_domain).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    template = FIELD_TEMPLATES[template_id]
    created_fields = []
    
    for field_data in template.fields:
        # Check if field already exists
        existing = db.query(CustomFieldDefinition).filter(
            and_(
                CustomFieldDefinition.store_id == store.id,
                CustomFieldDefinition.name == field_data.name
            )
        ).first()
        
        if not existing:
            field_dict = field_data.dict()
            if field_dict.get('validation_rules'):
                field_dict['validation_rules'] = field_dict['validation_rules'].dict()
            
            new_field = CustomFieldDefinition(
                store_id=store.id,
                **field_dict
            )
            db.add(new_field)
            created_fields.append(field_data.name)
    
    db.commit()
    
    # Log template application
    logger.info(f"Applied template {template_id} to store {shop_domain}, created {len(created_fields)} fields")
    
    return {
        "message": f"Template applied successfully",
        "template_id": template_id,
        "fields_created": len(created_fields),
        "field_names": created_fields
    }

@router.post("/bulk")
async def bulk_operations(
    operation: BulkOperation,
    shop_domain: str = Query(...),
    db: Session = Depends(get_db)
):
    """Perform bulk operations on custom fields"""
    store = db.query(Store).filter(Store.shopify_domain == shop_domain).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    results = {
        "operation": operation.operation,
        "success": [],
        "failed": [],
        "total": 0
    }
    
    if operation.operation == "create" and operation.field_data:
        for field_data in operation.field_data:
            try:
                field_dict = field_data.dict()
                if field_dict.get('validation_rules'):
                    field_dict['validation_rules'] = field_dict['validation_rules'].dict()
                
                new_field = CustomFieldDefinition(
                    store_id=store.id,
                    **field_dict
                )
                db.add(new_field)
                results["success"].append(field_data.name)
            except Exception as e:
                results["failed"].append({"field": field_data.name, "error": str(e)})
        
        db.commit()
        results["total"] = len(operation.field_data)
    
    elif operation.operation == "update" and operation.field_ids and operation.update_data:
        fields = db.query(CustomFieldDefinition).filter(
            and_(
                CustomFieldDefinition.store_id == store.id,
                CustomFieldDefinition.id.in_(operation.field_ids)
            )
        ).all()
        
        for field in fields:
            try:
                for key, value in operation.update_data.items():
                    if hasattr(field, key):
                        setattr(field, key, value)
                results["success"].append(field.id)
            except Exception as e:
                results["failed"].append({"field_id": field.id, "error": str(e)})
        
        db.commit()
        results["total"] = len(fields)
    
    elif operation.operation == "delete" and operation.field_ids:
        deleted = db.query(CustomFieldDefinition).filter(
            and_(
                CustomFieldDefinition.store_id == store.id,
                CustomFieldDefinition.id.in_(operation.field_ids)
            )
        ).delete(synchronize_session=False)
        
        db.commit()
        results["success"] = operation.field_ids
        results["total"] = deleted
    
    return results

@router.get("/{shop_domain}/search")
async def search_fields(
    shop_domain: str,
    q: str = Query(None, description="Search query"),
    field_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Advanced search for custom fields"""
    store = db.query(Store).filter(Store.shopify_domain == shop_domain).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    query = db.query(CustomFieldDefinition).filter(
        CustomFieldDefinition.store_id == store.id
    )
    
    # Apply filters
    if q:
        search_filter = or_(
            CustomFieldDefinition.name.ilike(f"%{q}%"),
            CustomFieldDefinition.label.ilike(f"%{q}%"),
            CustomFieldDefinition.description.ilike(f"%{q}%")
        )
        query = query.filter(search_filter)
    
    if field_type:
        query = query.filter(CustomFieldDefinition.field_type == field_type)
    
    if is_active is not None:
        query = query.filter(CustomFieldDefinition.is_active == is_active)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    fields = query.offset(offset).limit(limit).all()
    
    return {
        "fields": [
            {
                "id": field.id,
                "name": field.name,
                "field_type": field.field_type,
                "label": field.label,
                "description": field.description,
                "is_active": field.is_active,
                "created_at": field.created_at.isoformat() if field.created_at else None
            }
            for field in fields
        ],
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
    }

@router.get("/{shop_domain}/statistics")
# @cache_result(expire=300)
async def get_field_statistics(
    shop_domain: str,
    db: Session = Depends(get_db)
):
    """Get statistics about custom fields usage"""
    store = db.query(Store).filter(Store.shopify_domain == shop_domain).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    # Get field statistics
    total_fields = db.query(func.count(CustomFieldDefinition.id)).filter(
        CustomFieldDefinition.store_id == store.id
    ).scalar()
    
    active_fields = db.query(func.count(CustomFieldDefinition.id)).filter(
        and_(
            CustomFieldDefinition.store_id == store.id,
            CustomFieldDefinition.is_active == True
        )
    ).scalar()
    
    # Get fields by type
    fields_by_type = db.query(
        CustomFieldDefinition.field_type,
        func.count(CustomFieldDefinition.id).label('count')
    ).filter(
        CustomFieldDefinition.store_id == store.id
    ).group_by(CustomFieldDefinition.field_type).all()
    
    return {
        "total_fields": total_fields,
        "active_fields": active_fields,
        "inactive_fields": total_fields - active_fields,
        "fields_by_type": {
            field_type: count
            for field_type, count in fields_by_type
        },
        "usage_percentage": (active_fields / total_fields * 100) if total_fields > 0 else 0
    }

@router.post("/validate/{shop_domain}/{field_id}")
async def validate_field_value(
    shop_domain: str,
    field_id: int,
    value: Any,
    db: Session = Depends(get_db)
):
    """Validate a value against field rules"""
    store = db.query(Store).filter(Store.shopify_domain == shop_domain).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    field = db.query(CustomFieldDefinition).filter(
        and_(
            CustomFieldDefinition.store_id == store.id,
            CustomFieldDefinition.id == field_id
        )
    ).first()
    
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    
    validation_errors = []
    
    if field.validation_rules:
        rules = field.validation_rules
        
        # Required check
        if rules.get('required') and not value:
            validation_errors.append("Field is required")
        
        # Type-specific validation
        if field.field_type == 'number' and value is not None:
            try:
                num_value = float(value)
                if rules.get('min_value') is not None and num_value < rules['min_value']:
                    validation_errors.append(f"Value must be at least {rules['min_value']}")
                if rules.get('max_value') is not None and num_value > rules['max_value']:
                    validation_errors.append(f"Value must be at most {rules['max_value']}")
            except ValueError:
                validation_errors.append("Invalid number format")
        
        elif field.field_type == 'text' and value:
            if rules.get('min_length') and len(str(value)) < rules['min_length']:
                validation_errors.append(f"Minimum length is {rules['min_length']} characters")
            if rules.get('max_length') and len(str(value)) > rules['max_length']:
                validation_errors.append(f"Maximum length is {rules['max_length']} characters")
            if rules.get('pattern'):
                import re
                if not re.match(rules['pattern'], str(value)):
                    validation_errors.append("Value does not match required pattern")
        
        elif field.field_type == 'select' and value:
            if rules.get('allowed_values') and value not in rules['allowed_values']:
                validation_errors.append(f"Value must be one of: {', '.join(rules['allowed_values'])}")
    
    return {
        "field_id": field_id,
        "field_name": field.name,
        "value": value,
        "is_valid": len(validation_errors) == 0,
        "errors": validation_errors
    }
