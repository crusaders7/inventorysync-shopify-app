"""
Location Management API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional

router = APIRouter()

@router.get("/")
async def get_locations():
    """Get all locations"""
    return {
        "items": [
            {"id": "1", "name": "Warehouse A", "address": "123 Main St", "is_active": True},
            {"id": "2", "name": "Warehouse B", "address": "456 Oak Ave", "is_active": True}
        ],
        "total": 2
    }

@router.post("/")
async def create_location(data: Dict):
    """Create new location"""
    return {
        "id": "3",
        "name": data.get("name", "New Location"),
        "address": data.get("address", ""),
        "is_active": True,
        "message": "Location created successfully"
    }
