"""
Custom Fields API - Simple implementation for testing
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import re
from sqlalchemy.orm import Session
from database import get_db
from models import Store, CustomFieldDefinition

router = APIRouter(prefix="/api/custom-fields", tags=["custom-fields"])

class CustomFieldCreate(BaseModel):
    field_name: str
    field_type: str
    display_name: str
    description: Optional[str] = ""
    required: Optional[bool] = False
    is_required: Optional[bool] = False  # Alternative name for compatibility
    default_value: Optional[str] = ""
    validation_rules: Optional[Dict[str, Any]] = {}
    category: Optional[str] = "product"
    target_entity: Optional[str] = None  # Alternative name for category

class CustomFieldUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None

def get_store(shop_domain: str, db: Session) -> Optional[Store]:
    """Get store from domain"""
    return db.query(Store).filter(Store.shopify_domain == shop_domain).first()

def validate_field_name(field_name: str) -> bool:
    """Validate field name format"""
    return re.match(r'^[a-z][a-z0-9_]*$', field_name) is not None

@router.get("/templates")
async def get_custom_field_templates():
    """Get predefined custom field templates for different industries"""
    templates = {
        "apparel": [
            {
                "field_name": "size",
                "field_type": "select",
                "display_name": "Size",
                "options": ["XS", "S", "M", "L", "XL", "XXL"],
                "required": True
            },
            {
                "field_name": "color",
                "field_type": "text",
                "display_name": "Color",
                "required": True
            },
            {
                "field_name": "material",
                "field_type": "text",
                "display_name": "Material",
                "required": False
            },
            {
                "field_name": "season",
                "field_type": "select",
                "display_name": "Season",
                "options": ["Spring", "Summer", "Fall", "Winter"],
                "required": False
            }
        ],
        "electronics": [
            {
                "field_name": "warranty_period",
                "field_type": "number",
                "display_name": "Warranty Period (months)",
                "required": True
            },
            {
                "field_name": "specifications",
                "field_type": "json",
                "display_name": "Technical Specifications",
                "required": False
            },
            {
                "field_name": "compatibility",
                "field_type": "text",
                "display_name": "Compatible With",
                "required": False
            }
        ],
        "food_beverage": [
            {
                "field_name": "expiration_date",
                "field_type": "date",
                "display_name": "Expiration Date",
                "required": True
            },
            {
                "field_name": "batch_number",
                "field_type": "text",
                "display_name": "Batch Number",
                "required": True
            },
            {
                "field_name": "storage_temp",
                "field_type": "number",
                "display_name": "Storage Temperature (°C)",
                "required": True
            },
            {
                "field_name": "ingredients",
                "field_type": "text",
                "display_name": "Ingredients",
                "required": True
            }
        ]
    }
    
    return JSONResponse(content={
        "status": "success",
        "templates": templates,
        "industries": list(templates.keys())
    })

@router.post("/{shop_domain}")
async def create_custom_field(shop_domain: str, field_data: CustomFieldCreate, db: Session = Depends(get_db)):
    """Create a new custom field using SQLAlchemy"""
    # Get store
    store = get_store(shop_domain, db)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    # Validate field name
    if not validate_field_name(field_data.field_name):
        raise HTTPException(status_code=400, detail="Invalid field name format")
    
    # Handle alternative field names
    required = field_data.is_required if field_data.is_required is not None else field_data.required
    category = field_data.target_entity if field_data.target_entity else field_data.category

    # Create custom field definition
    new_field = CustomFieldDefinition(
        store_id=store.id,
        field_name=field_data.field_name,
        display_name=field_data.display_name,
        field_type=field_data.field_type,
        target_entity=category,  # This is "product", "variant", etc.
        is_required=required,
        default_value=field_data.default_value,
        validation_rules=field_data.validation_rules,
        help_text=field_data.description
    )

    try:
        db.add(new_field)
        db.commit()
        db.refresh(new_field)

        print(f"✅ Custom field created: {field_data.field_name} (ID: {new_field.id})")

        return JSONResponse(
            status_code=201,
            content={
                "status": "success",
                "message": "Custom field created",
                "field_id": new_field.id,
                "field_name": new_field.field_name,
                "field_type": new_field.field_type,
                "display_name": new_field.display_name,
                "is_active": new_field.is_active
            }
        )
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating custom field: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{shop_domain}")
async def list_custom_fields(shop_domain: str):
    """List all custom fields for a store"""
    try:
        # Get store ID
        store_id = get_store_id(shop_domain)
        if not store_id:
            raise HTTPException(status_code=404, detail="Store not found")
        
        # Get fields from database
        conn = sqlite3.connect('inventorysync_dev.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, field_name, field_type, display_name, description,
                       required, default_value, validation_rules, category,
                       created_at, updated_at
                FROM custom_field_definitions 
                WHERE store_id = ?
                ORDER BY created_at DESC
            """, (store_id,))
            
            fields = []
            for row in cursor.fetchall():
                fields.append({
                    "id": row[0],
                    "field_name": row[1],
                    "field_type": row[2],
                    "display_name": row[3],
                    "description": row[4],
                    "required": bool(row[5]),
                    "default_value": row[6],
                    "validation_rules": json.loads(row[7]) if row[7] else {},
                    "category": row[8],
                    "created_at": row[9],
                    "updated_at": row[10]
                })
            
            return JSONResponse(content={
                "status": "success",
                "fields": fields,
                "total": len(fields)
            })
            
        finally:
            conn.close()
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error listing custom fields: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Removed duplicate - templates route moved before parameterized routes

@router.get("/definitions/{shop_domain}")
async def get_field_definitions(shop_domain: str):
    """Get all field definitions for a shop (alias for list_custom_fields)"""
    return await list_custom_fields(shop_domain)

@router.put("/{shop_domain}/{field_id}")
async def update_custom_field(shop_domain: str, field_id: int, field_data: CustomFieldUpdate):
    """Update a custom field"""
    try:
        # Get store ID
        store_id = get_store_id(shop_domain)
        if not store_id:
            raise HTTPException(status_code=404, detail="Store not found")
        
        # Update database
        conn = sqlite3.connect('inventorysync_dev.db')
        cursor = conn.cursor()
        
        try:
            # Check if field exists
            cursor.execute("""
                SELECT id FROM custom_field_definitions 
                WHERE id = ? AND store_id = ?
            """, (field_id, store_id))
            
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Custom field not found")
            
            # Build update query
            update_fields = []
            update_values = []
            
            if field_data.display_name is not None:
                update_fields.append("display_name = ?")
                update_values.append(field_data.display_name)
            
            if field_data.description is not None:
                update_fields.append("description = ?")
                update_values.append(field_data.description)
            
            if field_data.validation_rules is not None:
                update_fields.append("validation_rules = ?")
                update_values.append(json.dumps(field_data.validation_rules))
            
            if update_fields:
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                update_values.append(field_id)
                
                query = f"""
                    UPDATE custom_field_definitions 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                """
                
                cursor.execute(query, update_values)
                conn.commit()
                
                print(f"✅ Custom field updated: {field_id}")
                
                return JSONResponse(content={
                    "status": "success",
                    "message": "Custom field updated",
                    "field_id": field_id
                })
            else:
                return JSONResponse(content={
                    "status": "success",
                    "message": "No changes to update",
                    "field_id": field_id
                })
            
        finally:
            conn.close()
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating custom field: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{shop_domain}/{field_id}")
async def delete_custom_field(shop_domain: str, field_id: int):
    """Delete a custom field"""
    try:
        # Get store ID
        store_id = get_store_id(shop_domain)
        if not store_id:
            raise HTTPException(status_code=404, detail="Store not found")
        
        # Delete from database
        conn = sqlite3.connect('inventorysync_dev.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                DELETE FROM custom_field_definitions 
                WHERE id = ? AND store_id = ?
            """, (field_id, store_id))
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Custom field not found")
            
            conn.commit()
            
            print(f"✅ Custom field deleted: {field_id}")
            
            return JSONResponse(content={
                "status": "success",
                "message": "Custom field deleted",
                "field_id": field_id
            })
            
        finally:
            conn.close()
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting custom field: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{shop_domain}/validate/{field_name}")
async def validate_field_value(shop_domain: str, field_name: str, value: str):
    """Validate a field value against its rules"""
    try:
        # Get store ID
        store_id = get_store_id(shop_domain)
        if not store_id:
            raise HTTPException(status_code=404, detail="Store not found")
        
        # Get field definition
        conn = sqlite3.connect('inventorysync_dev.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT field_type, validation_rules
                FROM custom_field_definitions 
                WHERE field_name = ? AND store_id = ?
            """, (field_name, store_id))
            
            result = cursor.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Field not found")
            
            field_type, validation_rules_json = result
            validation_rules = json.loads(validation_rules_json) if validation_rules_json else {}
            
            # Validate value
            is_valid = True
            errors = []
            
            if field_type == "text":
                if "max_length" in validation_rules and len(value) > validation_rules["max_length"]:
                    is_valid = False
                    errors.append(f"Value exceeds maximum length of {validation_rules['max_length']}")
                
                if "pattern" in validation_rules and not re.match(validation_rules["pattern"], value):
                    is_valid = False
                    errors.append("Value does not match required pattern")
            
            elif field_type == "number":
                try:
                    num_value = float(value)
                    if "min_value" in validation_rules and num_value < validation_rules["min_value"]:
                        is_valid = False
                        errors.append(f"Value is below minimum of {validation_rules['min_value']}")
                    
                    if "max_value" in validation_rules and num_value > validation_rules["max_value"]:
                        is_valid = False
                        errors.append(f"Value exceeds maximum of {validation_rules['max_value']}")
                except ValueError:
                    is_valid = False
                    errors.append("Value is not a valid number")
            
            return JSONResponse(content={
                "status": "success",
                "is_valid": is_valid,
                "errors": errors,
                "field_type": field_type,
                "validation_rules": validation_rules
            })
            
        finally:
            conn.close()
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error validating field value: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
