#!/usr/bin/env python3
"""
Create working custom fields API endpoints
"""

import os
import sys

# Create simplified custom fields API
custom_fields_api = '''"""
Custom Fields API - Simple implementation for testing
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import sqlite3
import re

router = APIRouter(prefix="/api/v1/custom-fields", tags=["custom-fields"])

class CustomFieldCreate(BaseModel):
    field_name: str
    field_type: str
    display_name: str
    description: Optional[str] = ""
    required: bool = False
    default_value: Optional[str] = ""
    validation_rules: Optional[Dict[str, Any]] = {}
    category: str = "product"

class CustomFieldUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None

def get_store_id(shop_domain: str) -> int:
    """Get store ID from domain"""
    conn = sqlite3.connect('inventorysync_dev.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM stores WHERE shopify_domain = ?", (shop_domain,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def validate_field_name(field_name: str) -> bool:
    """Validate field name format"""
    return re.match(r'^[a-z][a-z0-9_]*$', field_name) is not None

@router.post("/{shop_domain}")
async def create_custom_field(shop_domain: str, field_data: CustomFieldCreate):
    """Create a new custom field"""
    try:
        # Get store ID
        store_id = get_store_id(shop_domain)
        if not store_id:
            raise HTTPException(status_code=404, detail="Store not found")
        
        # Validate field name
        if not validate_field_name(field_data.field_name):
            raise HTTPException(status_code=400, detail="Invalid field name format")
        
        # Save to database
        conn = sqlite3.connect('inventorysync_dev.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO custom_field_definitions (
                    store_id, field_name, field_type, display_name, description,
                    required, default_value, validation_rules, category
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                store_id,
                field_data.field_name,
                field_data.field_type,
                field_data.display_name,
                field_data.description,
                field_data.required,
                field_data.default_value,
                json.dumps(field_data.validation_rules),
                field_data.category
            ))
            
            field_id = cursor.lastrowid
            conn.commit()
            
            print(f"✅ Custom field created: {field_data.field_name} (ID: {field_id})")
            
            return JSONResponse(content={
                "status": "success",
                "message": "Custom field created",
                "field_id": field_id,
                "field_name": field_data.field_name
            })
            
        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise HTTPException(status_code=409, detail="Field name already exists")
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail="Database error")
        finally:
            conn.close()
    
    except HTTPException:
        raise
    except Exception as e:
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
'''

def create_custom_fields_api():
    """Create custom fields API file"""
    
    # Write the new API
    api_file = "api/custom_fields.py"
    with open(api_file, 'w') as f:
        f.write(custom_fields_api)
    
    print(f"✅ Created custom fields API: {api_file}")

def main():
    """Main function"""
    print("🔄 Creating custom fields API...")
    
    create_custom_fields_api()
    
    print("\n✅ Custom fields API created successfully!")
    print("\n📝 API endpoints created:")
    print("- POST /api/custom-fields/{shop_domain} - Create field")
    print("- GET /api/custom-fields/{shop_domain} - List fields")
    print("- PUT /api/custom-fields/{shop_domain}/{field_id} - Update field")
    print("- DELETE /api/custom-fields/{shop_domain}/{field_id} - Delete field")
    print("- GET /api/custom-fields/{shop_domain}/validate/{field_name} - Validate value")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())