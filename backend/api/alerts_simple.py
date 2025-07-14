"""
Alerts API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional

router = APIRouter()

@router.get("/")
async def get_alerts():
    """Get all alerts"""
    return {
        "items": [
            {"id": "1", "type": "low_stock", "threshold": 10, "is_active": True}
        ],
        "total": 1
    }

@router.post("/")
async def create_alert(data: Dict):
    """Create new alert"""
    return {
        "id": "2",
        "type": data.get("type", "low_stock"),
        "threshold": data.get("threshold", 10),
        "is_active": True,
        "message": "Alert created successfully"
    }
