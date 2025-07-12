"""
Authentication API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from typing import Optional

router = APIRouter()

@router.get("/install")
async def install(shop: Optional[str] = Query(None)):
    """Shopify app installation endpoint"""
    if not shop:
        raise HTTPException(status_code=400, detail="Shop parameter required")
    
    # In production, this would redirect to Shopify OAuth
    # For testing, we'll return a redirect response
    return RedirectResponse(
        url=f"https://{shop}/admin/oauth/authorize?client_id=test&scope=read_inventory,write_inventory",
        status_code=307
    )

@router.get("/callback")
async def callback(
    code: Optional[str] = Query(None),
    shop: Optional[str] = Query(None),
    state: Optional[str] = Query(None)
):
    """Shopify OAuth callback endpoint"""
    if not code or not shop:
        raise HTTPException(status_code=422, detail="Missing required parameters")
    
    return {
        "status": "success",
        "shop": shop,
        "access_token": "test_access_token",
        "message": "Authentication successful"
    }
