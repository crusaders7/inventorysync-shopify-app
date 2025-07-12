"""
Industry Templates API - Simple version
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])

# Hardcoded templates data
INDUSTRY_TEMPLATES = {
    "apparel": {
        "name": "Apparel & Fashion",
        "description": "Custom fields for clothing and fashion retailers",
        "custom_fields": [
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
        ]
    },
    "electronics": {
        "name": "Electronics",
        "description": "Custom fields for electronics and tech products",
        "custom_fields": [
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
        ]
    },
    "food_beverage": {
        "name": "Food & Beverage",
        "description": "Custom fields for food and beverage products",
        "custom_fields": [
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
    },
    "jewelry": {
        "name": "Jewelry & Accessories",
        "description": "Custom fields for jewelry and luxury items",
        "custom_fields": [
            {
                "field_name": "metal_type",
                "field_type": "select",
                "display_name": "Metal Type",
                "options": ["Gold", "Silver", "Platinum", "Other"],
                "required": True
            },
            {
                "field_name": "stone_type",
                "field_type": "text",
                "display_name": "Stone Type",
                "required": False
            },
            {
                "field_name": "carat_weight",
                "field_type": "number",
                "display_name": "Carat Weight",
                "required": False
            }
        ]
    },
    "automotive": {
        "name": "Automotive Parts",
        "description": "Custom fields for auto parts and accessories",
        "custom_fields": [
            {
                "field_name": "part_number",
                "field_type": "text",
                "display_name": "Part Number",
                "required": True
            },
            {
                "field_name": "compatibility",
                "field_type": "text",
                "display_name": "Vehicle Compatibility",
                "required": True
            },
            {
                "field_name": "year_range",
                "field_type": "text",
                "display_name": "Year Range",
                "required": False
            }
        ]
    },
    "health_beauty": {
        "name": "Health & Beauty",
        "description": "Custom fields for cosmetics and health products",
        "custom_fields": [
            {
                "field_name": "ingredients",
                "field_type": "text",
                "display_name": "Ingredients",
                "required": True
            },
            {
                "field_name": "skin_type",
                "field_type": "select",
                "display_name": "Skin Type",
                "options": ["Normal", "Dry", "Oily", "Combination", "Sensitive"],
                "required": False
            },
            {
                "field_name": "expiry_date",
                "field_type": "date",
                "display_name": "Expiry Date",
                "required": True
            }
        ]
    }
}

@router.get("/industries")
async def list_industries():
    """Get list of available industry templates"""
    templates = []
    for industry_id, template in INDUSTRY_TEMPLATES.items():
        templates.append({
            "id": industry_id,
            "name": template["name"],
            "description": template["description"],
            "field_count": len(template["custom_fields"]),
            "workflow_count": 0
        })
    
    return JSONResponse(content={
        "templates": templates,
        "total": len(templates)
    })

@router.get("/industries/{industry}")
async def get_industry_template(industry: str):
    """Get detailed template for a specific industry"""
    template = INDUSTRY_TEMPLATES.get(industry)
    
    if not template:
        raise HTTPException(status_code=404, detail="Industry template not found")
    
    return JSONResponse(content={
        "industry": industry,
        "template": template
    })

@router.post("/apply/{industry}")
async def apply_industry_template(
    industry: str,
    shop: str = Query(..., description="Shop domain")
):
    """Apply an industry template to a store"""
    import sqlite3
    import json
    
    template = INDUSTRY_TEMPLATES.get(industry)
    if not template:
        raise HTTPException(status_code=404, detail="Industry template not found")
    
    try:
        # Connect to database
        conn = sqlite3.connect('inventorysync_dev.db')
        cursor = conn.cursor()
        
        # Get store
        cursor.execute("SELECT id FROM stores WHERE shop_domain = ?", (shop,))
        store = cursor.fetchone()
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        
        store_id = store[0]
        
        # Apply custom fields
        created_fields = []
        for field_config in template["custom_fields"]:
            # Check if field already exists
            cursor.execute("""
                SELECT id FROM custom_field_definitions 
                WHERE store_id = ? AND field_name = ? AND category = 'product'
            """, (store_id, field_config["field_name"]))
            
            if not cursor.fetchone():
                # Create new field
                cursor.execute("""
                    INSERT INTO custom_field_definitions (
                        store_id, field_name, field_type, display_name, 
                        description, required, validation_rules, category
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    store_id,
                    field_config["field_name"],
                    field_config["field_type"],
                    field_config["display_name"],
                    field_config.get("description", ""),
                    field_config.get("required", False),
                    json.dumps({"options": field_config.get("options", [])}),
                    "product"
                ))
                created_fields.append(field_config["field_name"])
        
        conn.commit()
        conn.close()
        
        return JSONResponse(content={
            "success": True,
            "industry": industry,
            "fields_created": len(created_fields),
            "fields": created_fields,
            "message": f"Successfully applied {template['name']} template"
        })
        
    except Exception as e:
        if conn:
            conn.close()
        print(f"Error applying template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to apply template: {str(e)}")
