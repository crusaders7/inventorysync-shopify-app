"""
Workflows API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional

router = APIRouter()

@router.get("/")
async def get_workflows():
    """Get all workflows"""
    return {
        "items": [
            {"id": "1", "name": "Low Stock Alert", "trigger": "low_stock", "is_active": True}
        ],
        "total": 1
    }

@router.post("/")
async def create_workflow(data: Dict):
    """Create new workflow"""
    return {
        "id": "2",
        "name": data.get("name", "New Workflow"),
        "trigger": data.get("trigger", "low_stock"),
        "actions": data.get("actions", []),
        "is_active": True,
        "message": "Workflow created successfully"
    }
