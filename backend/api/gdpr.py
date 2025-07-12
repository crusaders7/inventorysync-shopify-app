"""GDPR webhook handlers for Shopify compliance"""

from fastapi import APIRouter, Request, Response, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Dict, Any
import hmac
import hashlib
import base64
from datetime import datetime

from database import get_db
from models import Store, Product, Alert, InventoryItem
from utils.logging import logger
from config import settings

router = APIRouter(
    prefix="/api/v1/webhooks/gdpr",
    tags=["GDPR"],
)

def verify_webhook_signature(request_body: bytes, signature: str) -> bool:
    """Verify Shopify webhook signature"""
    if not settings.shopify_webhook_secret:
        logger.warning("No webhook secret configured")
        return False
    
    calculated_hmac = base64.b64encode(
        hmac.new(
            settings.shopify_webhook_secret.encode('utf-8'),
            request_body,
            digestmod=hashlib.sha256
        ).digest()
    ).decode()
    
    return hmac.compare_digest(calculated_hmac, signature)

@router.post("/customers_data_request")
async def handle_customers_data_request(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Response:
    """
    Handle customer data request webhook.
    This is called when a customer requests their data.
    """
    # Verify webhook
    body = await request.body()
    signature = request.headers.get("X-Shopify-Hmac-Sha256", "")
    
    if not verify_webhook_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    data = await request.json()
    shop_domain = data.get("shop_domain")
    customer_id = data.get("customer", {}).get("id")
    
    logger.info(
        "GDPR customer data request received",
        shop_domain=shop_domain,
        customer_id=customer_id
    )
    
    # In this app, we don't store customer-specific data
    # If we did, we would compile and send it to the customer
    
    # Log the request for compliance
    logger.security_event(
        "gdpr_data_request",
        shop_domain=shop_domain,
        customer_id=customer_id,
        timestamp=datetime.utcnow().isoformat()
    )
    
    return Response(status_code=200)

@router.post("/customers_redact")
async def handle_customers_redact(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Response:
    """
    Handle customer redaction webhook.
    This is called to delete customer data.
    """
    # Verify webhook
    body = await request.body()
    signature = request.headers.get("X-Shopify-Hmac-Sha256", "")
    
    if not verify_webhook_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    data = await request.json()
    shop_domain = data.get("shop_domain")
    customer_id = data.get("customer", {}).get("id")
    
    logger.info(
        "GDPR customer redaction request received",
        shop_domain=shop_domain,
        customer_id=customer_id
    )
    
    # Since we don't store customer data, there's nothing to redact
    # If we did store customer data, we would delete it here
    
    # Log the redaction for compliance
    logger.security_event(
        "gdpr_customer_redacted",
        shop_domain=shop_domain,
        customer_id=customer_id,
        timestamp=datetime.utcnow().isoformat()
    )
    
    return Response(status_code=200)

@router.post("/shop_redact")
async def handle_shop_redact(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Response:
    """
    Handle shop redaction webhook.
    This is called 48 hours after a shop uninstalls the app.
    """
    # Verify webhook
    body = await request.body()
    signature = request.headers.get("X-Shopify-Hmac-Sha256", "")
    
    if not verify_webhook_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    data = await request.json()
    shop_domain = data.get("shop_domain")
    
    logger.info(
        "GDPR shop redaction request received",
        shop_domain=shop_domain
    )
    
    try:
        # Find the store
        result = await db.execute(
            select(Store).where(Store.shopify_domain == shop_domain)
        )
        store = result.scalar_one_or_none()
        
        if store:
            # Delete all store data
            store_id = store.id
            
            # Delete alerts
            await db.execute(delete(Alert).where(Alert.store_id == store_id))
            
            # Delete inventory items
            await db.execute(delete(InventoryItem).where(InventoryItem.store_id == store_id))
            
            # Delete products
            await db.execute(delete(Product).where(Product.store_id == store_id))
            
            # Delete the store itself
            await db.delete(store)
            
            await db.commit()
            
            logger.info(
                "Shop data successfully redacted",
                shop_domain=shop_domain,
                store_id=store_id
            )
        else:
            logger.warning(
                "Shop not found for redaction",
                shop_domain=shop_domain
            )
        
        # Log the redaction for compliance
        logger.security_event(
            "gdpr_shop_redacted",
            shop_domain=shop_domain,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(
            "Error during shop redaction",
            shop_domain=shop_domain,
            error=str(e)
        )
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to redact shop data")
    
    return Response(status_code=200)
