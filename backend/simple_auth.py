"""
Simple OAuth Callback Handler
Works with existing database schema
"""

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, JSONResponse
import requests
from database import SessionLocal
from sqlalchemy import text
from config import settings
from utils.logging import logger
import json

router = APIRouter(prefix="/api/v1/auth", tags=["simple_auth"])

@router.get("/callback")
async def simple_auth_callback(
    shop: str = Query(...),
    code: str = Query(...),
    state: str = Query(None),
    hmac: str = Query(None),
    timestamp: str = Query(None)
):
    """
    Simple OAuth callback handler that works with current database schema
    """
    try:
        logger.info(f"OAuth callback received for shop: {shop}")
        
        # Validate shop domain
        if not shop.endswith('.myshopify.com'):
            shop = f"{shop}.myshopify.com"
        
        # Exchange code for access token
        token_url = f"https://{shop}/admin/oauth/access_token"
        token_data = {
            "client_id": settings.shopify_api_key,
            "client_secret": settings.shopify_api_secret,
            "code": code
        }
        
        logger.info(f"Exchanging code for access token for shop: {shop}")
        response = requests.post(token_url, json=token_data)
        
        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to exchange code for token: {response.text}"
            )
        
        token_response = response.json()
        access_token = token_response.get("access_token")
        
        if not access_token:
            logger.error("No access token received from Shopify")
            raise HTTPException(status_code=400, detail="No access token received")
        
        logger.info(f"Access token obtained for shop: {shop}")
        
        # Get shop information
        shop_info_url = f"https://{shop}/admin/api/2024-01/shop.json"
        headers = {"X-Shopify-Access-Token": access_token}
        
        shop_response = requests.get(shop_info_url, headers=headers)
        shop_data = {}
        
        if shop_response.status_code == 200:
            shop_data = shop_response.json().get("shop", {})
            logger.info(f"Shop info retrieved for: {shop_data.get('name', shop)}")
        
        # Update database using raw SQL (matching current schema)
        db = SessionLocal()
        try:
            # Check if store exists
            result = db.execute(
                text("SELECT id FROM stores WHERE shopify_domain = :shop"),
                {"shop": shop}
            ).fetchone()
            
            if result:
                # Update existing store
                db.execute(
                    text("""
                        UPDATE stores 
                        SET access_token = :token,
                            shop_name = :name,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE shopify_domain = :shop
                    """),
                    {
                        "token": access_token,
                        "name": shop_data.get("name", shop),
                        "shop": shop
                    }
                )
                store_id = result[0]
                logger.info(f"Updated existing store ID: {store_id}")
            else:
                # Create new store
                db.execute(
                    text("""
                        INSERT INTO stores (shopify_domain, access_token, shop_name, email)
                        VALUES (:shop, :token, :name, :email)
                    """),
                    {
                        "shop": shop,
                        "token": access_token,
                        "name": shop_data.get("name", shop),
                        "email": shop_data.get("email", f"admin@{shop}")
                    }
                )
                # Get the new store ID
                result = db.execute(
                    text("SELECT id FROM stores WHERE shopify_domain = :shop"),
                    {"shop": shop}
                ).fetchone()
                store_id = result[0]
                logger.info(f"Created new store ID: {store_id}")
            
            db.commit()
            
            # Return success response
            return JSONResponse({
                "status": "success",
                "message": "OAuth completed successfully!",
                "shop": shop,
                "store_id": store_id,
                "shop_name": shop_data.get("name", shop),
                "next_steps": [
                    "Your store is now connected to InventorySync",
                    "You can close this window and return to your store admin",
                    f"Access your store at: https://{shop}/admin"
                ]
            })
            
        except Exception as db_error:
            db.rollback()
            logger.error(f"Database error: {db_error}")
            raise HTTPException(
                status_code=500, 
                detail=f"Database error: {str(db_error)}"
            )
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"OAuth callback failed: {str(e)}"
        )

@router.get("/status")
async def auth_status():
    """Check authentication status"""
    return {
        "status": "ready",
        "callback_url": "http://localhost:8000/api/v1/auth/callback",
        "message": "OAuth handler is ready"
    }