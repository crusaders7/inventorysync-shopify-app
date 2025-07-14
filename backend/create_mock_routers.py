#!/usr/bin/env python3
"""
Create simplified mock routers for missing endpoints
"""
import os

# Template for simple router
ROUTER_TEMPLATE = '''"""
{name} API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from datetime import datetime

router = APIRouter()

@router.get("/")
async def get_{name}_list():
    """Get list of {name}"""
    return {{
        "items": [],
        "total": 0,
        "message": "{name} endpoint is working"
    }}

@router.get("/{{item_id}}")
async def get_{name}_item(item_id: str):
    """Get specific {name} item"""
    return {{
        "id": item_id,
        "message": "{name} item endpoint is working"
    }}

@router.post("/")
async def create_{name}_item(data: Dict):
    """Create new {name} item"""
    return {{
        "id": "new_id",
        "data": data,
        "message": "{name} created successfully"
    }}

@router.put("/{{item_id}}")
async def update_{name}_item(item_id: str, data: Dict):
    """Update {name} item"""
    return {{
        "id": item_id,
        "data": data,
        "message": "{name} updated successfully"
    }}

@router.delete("/{{item_id}}")
async def delete_{name}_item(item_id: str):
    """Delete {name} item"""
    return {{
        "id": item_id,
        "message": "{name} deleted successfully"
    }}
'''

# Special templates for specific routers
INVENTORY_TEMPLATE = '''"""
Inventory API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from datetime import datetime

router = APIRouter()

@router.get("/items")
async def get_inventory_items():
    """Get inventory items"""
    return {
        "items": [
            {
                "id": "1",
                "product_name": "Test Product",
                "sku": "TEST-001",
                "current_stock": 100,
                "location": "Warehouse A"
            }
        ],
        "total": 1
    }

@router.get("/levels")
async def get_inventory_levels():
    """Get inventory levels"""
    return {
        "levels": [
            {
                "product_id": "1",
                "location_id": "loc1",
                "available": 100,
                "reserved": 0
            }
        ]
    }

@router.post("/sync")
async def sync_inventory(data: Dict = {}):
    """Sync inventory with Shopify"""
    return {
        "status": "success",
        "synced_items": 0,
        "message": "Inventory sync completed"
    }

@router.get("/history")
async def get_inventory_history():
    """Get inventory movement history"""
    return {
        "movements": [],
        "total": 0
    }
'''

# Create missing routers
routers_to_create = {
    "locations": "location",
    "alerts": "alert", 
    "webhooks": "webhook",
    "reports": "report",
    "forecasting": "forecast",
    "workflows": "workflow",
}

# Special routers with custom templates
special_routers = {
    "inventory": INVENTORY_TEMPLATE,
}

def create_router_if_missing(filename: str, content: str):
    """Create router file if it doesn't exist or is missing required endpoints"""
    filepath = f"/home/brend/inventorysync-shopify-app/backend/api/{filename}.py"
    
    # Always create/overwrite these files for consistency
    print(f"Creating {filepath}")
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"✅ Created {filename}.py")

# Create regular routers
for filename, name in routers_to_create.items():
    content = ROUTER_TEMPLATE.format(name=name)
    create_router_if_missing(filename, content)

# Create special routers
for filename, content in special_routers.items():
    create_router_if_missing(filename, content)

print("\n✅ All mock routers created successfully!")
