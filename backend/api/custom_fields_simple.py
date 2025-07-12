"""
Simplified Custom Fields API - Core Feature of InventorySync
Allows Basic Shopify tier merchants to add custom fields without expensive upgrades
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional, Any
from datetime import datetime

router = APIRouter(prefix="/api/custom-fields", tags=["custom-fields"])

# In-memory storage for demo (replace with database in production)
custom_fields_store = {}

@router.get("/")
async def list_all_custom_fields():
    """List all custom fields across all shops"""
    return {
        "fields": list(custom_fields_store.values()),
        "total": len(custom_fields_store)
    }

@router.get("/value-proposition")
async def get_value_proposition():
    """Explain the value of custom fields feature"""
    return {
        "feature": "Unlimited Custom Fields",
        "our_price": "$29-99/month",
        "shopify_plus_price": "$2,000+/month",
        "monthly_savings": "$1,901-1,971",
        "annual_savings": "$22,812-23,652",
        "benefits": [
            "Add unlimited custom fields to products",
            "Create fields for any data type (text, number, date, etc.)",
            "Use pre-built industry templates",
            "No coding required",
            "Works with Basic Shopify plan",
            "Save 95% compared to Shopify Plus"
        ],
        "use_cases": [
            "Add size charts to apparel",
            "Track expiry dates for food products",
            "Store warranty info for electronics",
            "Add care instructions",
            "Track supplier information",
            "Store compliance data",
            "Add SEO metadata"
        ]
    }

@router.get("/templates")
async def get_field_templates():
    """Get pre-built field templates for different industries"""
    return {
        "templates": {
            "apparel": [
                {"field_name": "size", "display_name": "Size", "field_type": "select", "options": ["XS", "S", "M", "L", "XL"]},
                {"field_name": "color", "display_name": "Color", "field_type": "text"},
                {"field_name": "material", "display_name": "Material", "field_type": "text"},
                {"field_name": "care_instructions", "display_name": "Care Instructions", "field_type": "textarea"}
            ],
            "electronics": [
                {"field_name": "warranty_period", "display_name": "Warranty (months)", "field_type": "number"},
                {"field_name": "voltage", "display_name": "Voltage", "field_type": "text"},
                {"field_name": "compatibility", "display_name": "Compatible With", "field_type": "text"}
            ],
            "food_beverage": [
                {"field_name": "expiry_date", "display_name": "Expiry Date", "field_type": "date"},
                {"field_name": "ingredients", "display_name": "Ingredients", "field_type": "textarea"},
                {"field_name": "allergens", "display_name": "Allergens", "field_type": "multi_select"},
                {"field_name": "storage_temp", "display_name": "Storage Temperature", "field_type": "text"}
            ],
            "jewelry": [
                {"field_name": "metal_type", "display_name": "Metal Type", "field_type": "select"},
                {"field_name": "stone_type", "display_name": "Stone Type", "field_type": "text"},
                {"field_name": "carat_weight", "display_name": "Carat Weight", "field_type": "number"},
                {"field_name": "ring_size", "display_name": "Ring Size", "field_type": "select"}
            ]
        },
        "message": "Apply any template to start using custom fields immediately!"
    }

@router.get("/{shop_domain}")
async def get_shop_custom_fields(shop_domain: str):
    """Get all custom fields for a specific shop"""
    shop_fields = [
        field for field in custom_fields_store.values()
        if field.get("shop_domain") == shop_domain
    ]
    
    return {
        "shop_domain": shop_domain,
        "fields": shop_fields,
        "total": len(shop_fields),
        "pricing_tier_value": f"This feature would cost $200+/month on Shopify Plus!"
    }

@router.post("/{shop_domain}")
async def create_custom_field(shop_domain: str, field_data: Dict[str, Any]):
    """Create a new custom field for products"""
    field_id = f"{shop_domain}_{field_data.get('field_name', 'field')}_{datetime.now().timestamp()}"
    
    new_field = {
        "id": field_id,
        "shop_domain": shop_domain,
        "field_name": field_data.get("field_name", ""),
        "display_name": field_data.get("display_name", ""),
        "field_type": field_data.get("field_type", "text"),
        "target_entity": field_data.get("target_entity", "product"),
        "is_required": field_data.get("is_required", False),
        "validation_rules": field_data.get("validation_rules", {}),
        "created_at": datetime.now().isoformat(),
        "value_proposition": "Basic Shopify: $29/month vs Shopify Plus: $2000+/month"
    }
    
    custom_fields_store[field_id] = new_field
    
    return {
        "status": "success",
        "message": f"Custom field '{field_data.get('display_name')}' created successfully!",
        "field": new_field,
        "savings": "You just saved $1,971/month by using InventorySync!"
    }

@router.get("/templates")
async def get_field_templates():
    """Get pre-built field templates for different industries"""
    return {
        "templates": {
            "apparel": [
                {"field_name": "size", "display_name": "Size", "field_type": "select", "options": ["XS", "S", "M", "L", "XL"]},
                {"field_name": "color", "display_name": "Color", "field_type": "text"},
                {"field_name": "material", "display_name": "Material", "field_type": "text"},
                {"field_name": "care_instructions", "display_name": "Care Instructions", "field_type": "textarea"}
            ],
            "electronics": [
                {"field_name": "warranty_period", "display_name": "Warranty (months)", "field_type": "number"},
                {"field_name": "voltage", "display_name": "Voltage", "field_type": "text"},
                {"field_name": "compatibility", "display_name": "Compatible With", "field_type": "text"}
            ],
            "food_beverage": [
                {"field_name": "expiry_date", "display_name": "Expiry Date", "field_type": "date"},
                {"field_name": "ingredients", "display_name": "Ingredients", "field_type": "textarea"},
                {"field_name": "allergens", "display_name": "Allergens", "field_type": "multi_select"},
                {"field_name": "storage_temp", "display_name": "Storage Temperature", "field_type": "text"}
            ],
            "jewelry": [
                {"field_name": "metal_type", "display_name": "Metal Type", "field_type": "select"},
                {"field_name": "stone_type", "display_name": "Stone Type", "field_type": "text"},
                {"field_name": "carat_weight", "display_name": "Carat Weight", "field_type": "number"},
                {"field_name": "ring_size", "display_name": "Ring Size", "field_type": "select"}
            ]
        },
        "message": "Apply any template to start using custom fields immediately!"
    }

@router.post("/templates/{template_name}/apply/{shop_domain}")
async def apply_template(template_name: str, shop_domain: str):
    """Apply a pre-built template to a shop"""
    templates = await get_field_templates()
    
    if template_name not in templates["templates"]:
        raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
    
    template_fields = templates["templates"][template_name]
    created_fields = []
    
    for field_template in template_fields:
        field_data = {**field_template, "target_entity": "product"}
        result = await create_custom_field(shop_domain, field_data)
        created_fields.append(result["field"])
    
    return {
        "status": "success",
        "message": f"Applied {template_name} template with {len(created_fields)} custom fields",
        "fields_created": len(created_fields),
        "monthly_savings": "$1,971",
        "annual_savings": "$23,652"
    }

@router.delete("/{shop_domain}/{field_id}")
async def delete_custom_field(shop_domain: str, field_id: str):
    """Delete a custom field"""
    if field_id in custom_fields_store:
        del custom_fields_store[field_id]
        return {
            "status": "success",
            "message": "Custom field deleted successfully"
        }
    else:
        raise HTTPException(status_code=404, detail="Field not found")

