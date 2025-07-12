"""
Shopify Metafields API - Core integration for custom fields in Shopify admin
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import httpx
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/metafields")

# In-memory storage for demo (replace with database in production)
metafield_definitions = {}
shop_metafields = {}

# Pydantic models
class MetafieldDefinition(BaseModel):
    """Definition for a custom field that will appear in Shopify admin"""
    id: Optional[str] = None
    name: str = Field(..., description="Display name for the field")
    key: str = Field(..., description="Unique identifier for the field")
    namespace: str = Field(default="inventorysync", description="Namespace for grouping fields")
    type: str = Field(..., description="Field type: single_line_text_field, multi_line_text_field, number_integer, number_decimal, date, boolean, json")
    description: Optional[str] = Field(None, description="Help text for the field")
    validations: Optional[Dict[str, Any]] = Field(None, description="Validation rules")
    owner_type: str = Field(default="PRODUCT", description="Where this field appears: PRODUCT, VARIANT, CUSTOMER, etc.")
    
class MetafieldValue(BaseModel):
    """Value for a metafield on a specific resource"""
    resource_id: str = Field(..., description="Shopify product/variant ID")
    resource_type: str = Field(default="product", description="Type of resource")
    definition_id: str = Field(..., description="ID of the metafield definition")
    value: Any = Field(..., description="The actual value")
    
class BulkMetafieldUpdate(BaseModel):
    """Bulk update multiple metafields"""
    resource_ids: List[str] = Field(..., description="List of product IDs to update")
    updates: Dict[str, Any] = Field(..., description="Field key -> value mapping")

# Shopify metafield type mapping
SHOPIFY_METAFIELD_TYPES = {
    "text": "single_line_text_field",
    "multiline": "multi_line_text_field", 
    "number": "number_decimal",
    "integer": "number_integer",
    "date": "date",
    "boolean": "boolean",
    "json": "json",
    "url": "url",
    "color": "color",
    "weight": "weight",
    "volume": "volume",
    "dimension": "dimension"
}

# Industry templates
INDUSTRY_TEMPLATES = {
    "fashion": {
        "name": "Fashion & Apparel",
        "fields": [
            {"name": "Material", "key": "material", "type": "text", "description": "Primary material composition"},
            {"name": "Care Instructions", "key": "care_instructions", "type": "multiline", "description": "Washing and care guidelines"},
            {"name": "Fit Type", "key": "fit_type", "type": "text", "description": "Slim, Regular, Relaxed, etc."},
            {"name": "Season", "key": "season", "type": "text", "description": "Spring/Summer, Fall/Winter"},
            {"name": "Country of Origin", "key": "country_origin", "type": "text", "description": "Manufacturing country"}
        ]
    },
    "electronics": {
        "name": "Electronics & Tech",
        "fields": [
            {"name": "Battery Life", "key": "battery_life", "type": "text", "description": "Battery duration in hours"},
            {"name": "Warranty Period", "key": "warranty_period", "type": "text", "description": "Warranty duration"},
            {"name": "Specifications", "key": "specifications", "type": "json", "description": "Technical specifications"},
            {"name": "Compatibility", "key": "compatibility", "type": "multiline", "description": "Compatible devices/systems"},
            {"name": "Certifications", "key": "certifications", "type": "text", "description": "FCC, CE, etc."}
        ]
    },
    "food_beverage": {
        "name": "Food & Beverage",
        "fields": [
            {"name": "Ingredients", "key": "ingredients", "type": "multiline", "description": "Full ingredient list"},
            {"name": "Allergens", "key": "allergens", "type": "text", "description": "Contains: nuts, dairy, etc."},
            {"name": "Nutritional Info", "key": "nutrition", "type": "json", "description": "Per serving nutritional data"},
            {"name": "Best Before", "key": "best_before", "type": "date", "description": "Expiration date"},
            {"name": "Storage Instructions", "key": "storage", "type": "text", "description": "Storage requirements"}
        ]
    },
    "beauty": {
        "name": "Beauty & Cosmetics",
        "fields": [
            {"name": "Ingredients", "key": "ingredients", "type": "multiline", "description": "Full INCI list"},
            {"name": "Skin Type", "key": "skin_type", "type": "text", "description": "Suitable for: oily, dry, combination"},
            {"name": "Usage Instructions", "key": "usage", "type": "multiline", "description": "How to apply/use"},
            {"name": "Volume/Size", "key": "volume", "type": "text", "description": "Product volume or size"},
            {"name": "Cruelty Free", "key": "cruelty_free", "type": "boolean", "description": "Not tested on animals"}
        ]
    },
    "home_garden": {
        "name": "Home & Garden", 
        "fields": [
            {"name": "Dimensions", "key": "dimensions", "type": "text", "description": "L x W x H measurements"},
            {"name": "Assembly Required", "key": "assembly_required", "type": "boolean", "description": "Requires assembly"},
            {"name": "Material", "key": "material", "type": "text", "description": "Primary materials used"},
            {"name": "Care Instructions", "key": "care", "type": "multiline", "description": "Maintenance guidelines"},
            {"name": "Weight Capacity", "key": "weight_capacity", "type": "text", "description": "Maximum load"}
        ]
    }
}

@router.get("/")
async def get_metafields_info():
    """Get information about the metafields API"""
    return {
        "message": "InventorySync Metafields API - Add custom fields to Shopify products",
        "endpoints": {
            "definitions": "/api/metafields/definitions - Manage field definitions",
            "values": "/api/metafields/values - Get/set field values", 
            "templates": "/api/metafields/templates - Industry templates",
            "bulk": "/api/metafields/bulk - Bulk operations"
        },
        "supported_types": list(SHOPIFY_METAFIELD_TYPES.keys()),
        "value_proposition": "Save $1,971/month vs Shopify Plus!"
    }

@router.get("/definitions")
async def list_metafield_definitions(shop: str = Query(..., description="Shop domain")):
    """List all metafield definitions for a shop"""
    shop_defs = metafield_definitions.get(shop, [])
    return {
        "definitions": shop_defs,
        "count": len(shop_defs),
        "message": f"Custom field definitions for {shop}"
    }

@router.post("/definitions")
async def create_metafield_definition(
    definition: MetafieldDefinition,
    shop: str = Query(..., description="Shop domain")
):
    """Create a new metafield definition"""
    # Generate ID
    definition.id = f"gid://shopify/MetafieldDefinition/{len(metafield_definitions.get(shop, [])) + 1}"
    
    # Map to Shopify type
    if definition.type in SHOPIFY_METAFIELD_TYPES:
        definition.type = SHOPIFY_METAFIELD_TYPES[definition.type]
    
    # Store definition
    if shop not in metafield_definitions:
        metafield_definitions[shop] = []
    metafield_definitions[shop].append(definition.dict())
    
    logger.info(f"Created metafield definition: {definition.name} for shop: {shop}")
    
    return {
        "success": True,
        "definition": definition.dict(),
        "message": f"Custom field '{definition.name}' created successfully!"
    }

@router.delete("/definitions/{definition_id}")
async def delete_metafield_definition(
    definition_id: str,
    shop: str = Query(..., description="Shop domain")
):
    """Delete a metafield definition"""
    if shop in metafield_definitions:
        metafield_definitions[shop] = [
            d for d in metafield_definitions[shop] if d.get("id") != definition_id
        ]
    
    return {
        "success": True,
        "message": "Metafield definition deleted"
    }

@router.get("/values/{resource_id}")
async def get_metafield_values(
    resource_id: str,
    shop: str = Query(..., description="Shop domain")
):
    """Get all metafield values for a product"""
    key = f"{shop}:{resource_id}"
    values = shop_metafields.get(key, {})
    
    return {
        "resource_id": resource_id,
        "values": values,
        "count": len(values)
    }

@router.post("/values")
async def set_metafield_value(
    value: MetafieldValue,
    shop: str = Query(..., description="Shop domain")
):
    """Set a metafield value for a product"""
    key = f"{shop}:{value.resource_id}"
    
    if key not in shop_metafields:
        shop_metafields[key] = {}
    
    # Find the definition to get the field key
    definition = None
    for d in metafield_definitions.get(shop, []):
        if d.get("id") == value.definition_id:
            definition = d
            break
    
    if not definition:
        raise HTTPException(status_code=404, detail="Metafield definition not found")
    
    shop_metafields[key][definition["key"]] = {
        "value": value.value,
        "updated_at": datetime.utcnow().isoformat(),
        "definition_id": value.definition_id
    }
    
    return {
        "success": True,
        "message": f"Custom field value updated for {value.resource_id}"
    }

@router.post("/bulk")
async def bulk_update_metafields(
    bulk_update: BulkMetafieldUpdate,
    shop: str = Query(..., description="Shop domain")
):
    """Update metafields for multiple products at once"""
    updated_count = 0
    
    for resource_id in bulk_update.resource_ids:
        key = f"{shop}:{resource_id}"
        if key not in shop_metafields:
            shop_metafields[key] = {}
        
        for field_key, field_value in bulk_update.updates.items():
            shop_metafields[key][field_key] = {
                "value": field_value,
                "updated_at": datetime.utcnow().isoformat()
            }
        updated_count += 1
    
    return {
        "success": True,
        "updated_count": updated_count,
        "message": f"Updated custom fields for {updated_count} products"
    }

@router.get("/templates")
async def list_templates():
    """List available industry templates"""
    return {
        "templates": [
            {
                "id": key,
                "name": template["name"],
                "field_count": len(template["fields"]),
                "fields": template["fields"]
            }
            for key, template in INDUSTRY_TEMPLATES.items()
        ],
        "message": "Quick-start templates for common industries"
    }

@router.post("/templates/{template_id}/apply")
async def apply_template(
    template_id: str,
    shop: str = Query(..., description="Shop domain")
):
    """Apply an industry template to create multiple field definitions"""
    if template_id not in INDUSTRY_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template = INDUSTRY_TEMPLATES[template_id]
    created_fields = []
    
    for field in template["fields"]:
        definition = MetafieldDefinition(
            name=field["name"],
            key=field["key"],
            type=field["type"],
            description=field.get("description")
        )
        
        # Generate ID
        definition.id = f"gid://shopify/MetafieldDefinition/{len(metafield_definitions.get(shop, [])) + len(created_fields) + 1}"
        
        # Map to Shopify type
        if definition.type in SHOPIFY_METAFIELD_TYPES:
            definition.type = SHOPIFY_METAFIELD_TYPES[definition.type]
        
        created_fields.append(definition.dict())
    
    # Store all definitions
    if shop not in metafield_definitions:
        metafield_definitions[shop] = []
    metafield_definitions[shop].extend(created_fields)
    
    return {
        "success": True,
        "template": template["name"],
        "created_fields": created_fields,
        "message": f"Applied {template['name']} template - {len(created_fields)} custom fields created!"
    }

@router.get("/export")
async def export_metafields(
    shop: str = Query(..., description="Shop domain"),
    format: str = Query("json", description="Export format: json or csv")
):
    """Export all metafield definitions and values"""
    definitions = metafield_definitions.get(shop, [])
    all_values = {}
    
    # Collect all values
    for key, values in shop_metafields.items():
        if key.startswith(f"{shop}:"):
            resource_id = key.split(":", 1)[1]
            all_values[resource_id] = values
    
    export_data = {
        "shop": shop,
        "exported_at": datetime.utcnow().isoformat(),
        "definitions": definitions,
        "values": all_values
    }
    
    if format == "csv":
        # Simple CSV format
        csv_lines = ["Product ID,Field,Value"]
        for resource_id, fields in all_values.items():
            for field_key, field_data in fields.items():
                csv_lines.append(f"{resource_id},{field_key},{field_data['value']}")
        
        return {
            "format": "csv",
            "data": "\n".join(csv_lines)
        }
    
    return export_data

@router.post("/import")
async def import_metafields(
    data: Dict[str, Any],
    shop: str = Query(..., description="Shop domain")
):
    """Import metafield definitions and values"""
    imported_definitions = 0
    imported_values = 0
    
    # Import definitions
    if "definitions" in data:
        metafield_definitions[shop] = data["definitions"]
        imported_definitions = len(data["definitions"])
    
    # Import values
    if "values" in data:
        for resource_id, fields in data["values"].items():
            key = f"{shop}:{resource_id}"
            shop_metafields[key] = fields
            imported_values += 1
    
    return {
        "success": True,
        "imported_definitions": imported_definitions,
        "imported_values": imported_values,
        "message": f"Imported {imported_definitions} field definitions and values for {imported_values} products"
    }

# Health check
@router.get("/health")
async def metafields_health():
    """Check metafields API health"""
    return {
        "status": "healthy",
        "message": "Metafields API is running",
        "stats": {
            "shops": len(metafield_definitions),
            "total_definitions": sum(len(defs) for defs in metafield_definitions.values()),
            "total_values": len(shop_metafields)
        }
    }
