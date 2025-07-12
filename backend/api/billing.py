"""
Billing API Endpoints
Handles Shopify subscription management
"""

from fastapi import APIRouter, HTTPException, Query, Request, Depends, BackgroundTasks
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from database import AsyncSessionLocal
from models import Store
from shopify_billing import ShopifyBillingClient, BillingPlanManager, initialize_billing_for_store
from config import settings
from utils.logging import logger

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


@router.post("/subscribe/{plan_name}")
async def create_subscription(
    plan_name: str,
    shop: str = Query(..., description="Shop domain"),
    request: Request = None
):
    """Create a new subscription for a shop"""
    
    # Validate plan exists
    if plan_name not in BillingPlanManager.PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan name")
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Initialize billing
            confirmation_url = await initialize_billing_for_store(
                shop_domain=shop,
                access_token=store.access_token,
                plan=plan_name
            )
            
            if not confirmation_url:
                raise HTTPException(status_code=500, detail="Failed to create subscription")
            
            # Update store with pending subscription
            store.subscription_plan = plan_name
            store.subscription_status = "pending"
            await session.commit()
            
            logger.info(
                f"Created subscription for {shop}",
                shop_domain=shop,
                plan=plan_name
            )
            
            # Redirect to Shopify billing confirmation
            return RedirectResponse(url=confirmation_url)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscription creation failed: {e}")
        raise HTTPException(status_code=500, detail="Subscription creation failed")


@router.get("/callback")
async def billing_callback(
    shop: str = Query(...),
    charge_id: str = Query(...),
    request: Request = None
):
    """Handle billing callback from Shopify"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Get store
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Get charge details from Shopify
            billing_client = ShopifyBillingClient(shop, store.access_token)
            charge = await billing_client.get_charge(charge_id)
            
            # Check if charge was accepted
            if charge["status"] == "accepted":
                # Activate the charge
                activated_charge = await billing_client.activate_charge(charge_id)
                
                # Update store subscription
                store.shopify_charge_id = charge_id
                store.subscription_status = "active"
                store.billing_cycle_start = datetime.now()
                store.billing_cycle_end = datetime.now() + timedelta(days=30)
                store.plan_price = float(charge["price"])
                store.billing_currency = charge.get("currency", "USD")
                
                # Set trial end if applicable
                if charge.get("trial_days", 0) > 0:
                    store.trial_ends_at = datetime.now() + timedelta(days=charge["trial_days"])
                
                await session.commit()
                
                logger.info(
                    f"Activated subscription for {shop}",
                    shop_domain=shop,
                    charge_id=charge_id,
                    plan=store.subscription_plan
                )
                
                # Redirect to app dashboard
                dashboard_url = f"{settings.frontend_url}/?shop={shop}&billing=success"
                return RedirectResponse(url=dashboard_url)
                
            elif charge["status"] == "declined":
                # Handle declined payment
                store.subscription_status = "cancelled"
                await session.commit()
                
                error_url = f"{settings.frontend_url}/?shop={shop}&billing=declined"
                return RedirectResponse(url=error_url)
            
            else:
                # Pending or other status
                pending_url = f"{settings.frontend_url}/?shop={shop}&billing=pending"
                return RedirectResponse(url=pending_url)
                
    except Exception as e:
        logger.error(f"Billing callback failed: {e}")
        error_url = f"{settings.frontend_url}/?shop={shop}&billing=error"
        return RedirectResponse(url=error_url)


@router.get("/status/{shop}")
async def get_billing_status(shop: str):
    """Get current billing status for a shop"""
    
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Get plan details
            plan_details = BillingPlanManager.get_plan_details(store.subscription_plan)
            
            # Check if trial is active
            trial_active = False
            trial_days_left = 0
            if store.trial_ends_at and store.trial_ends_at > datetime.now():
                trial_active = True
                trial_days_left = (store.trial_ends_at - datetime.now()).days
            
            # Calculate usage
            usage_stats = await calculate_usage_stats(session, store.id)
            
            # Check for upgrade recommendations
            upgrade_recommendation = BillingPlanManager.get_upgrade_recommendation(
                store.subscription_plan, 
                usage_stats
            )
            
            return {
                "subscription_status": store.subscription_status,
                "plan": store.subscription_plan,
                "plan_details": plan_details,
                "price": store.plan_price,
                "currency": store.billing_currency,
                "trial_active": trial_active,
                "trial_days_left": trial_days_left,
                "billing_cycle_start": store.billing_cycle_start.isoformat() if store.billing_cycle_start else None,
                "billing_cycle_end": store.billing_cycle_end.isoformat() if store.billing_cycle_end else None,
                "usage": usage_stats,
                "upgrade_recommendation": upgrade_recommendation,
                "shopify_charge_id": store.shopify_charge_id
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get billing status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get billing status")


@router.post("/upgrade/{new_plan}")
async def upgrade_subscription(
    new_plan: str,
    shop: str = Query(...),
):
    """Upgrade subscription to a higher plan"""
    
    if new_plan not in BillingPlanManager.PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan name")
    
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Cancel current subscription
            if store.shopify_charge_id:
                billing_client = ShopifyBillingClient(shop, store.access_token)
                await billing_client.cancel_charge(store.shopify_charge_id)
            
            # Create new subscription
            confirmation_url = await initialize_billing_for_store(
                shop_domain=shop,
                access_token=store.access_token,
                plan=new_plan
            )
            
            if not confirmation_url:
                raise HTTPException(status_code=500, detail="Failed to create new subscription")
            
            logger.info(
                f"Upgrading subscription for {shop}",
                shop_domain=shop,
                old_plan=store.subscription_plan,
                new_plan=new_plan
            )
            
            return {"confirmation_url": confirmation_url}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscription upgrade failed: {e}")
        raise HTTPException(status_code=500, detail="Subscription upgrade failed")


@router.post("/cancel")
async def cancel_subscription(shop: str = Query(...)):
    """Cancel current subscription"""
    
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")
            
            # Cancel Shopify charge
            if store.shopify_charge_id:
                billing_client = ShopifyBillingClient(shop, store.access_token)
                success = await billing_client.cancel_charge(store.shopify_charge_id)
                
                if success:
                    store.subscription_status = "cancelled"
                    store.shopify_charge_id = None
                    await session.commit()
                    
                    logger.info(f"Cancelled subscription for {shop}")
                    return {"status": "cancelled"}
                else:
                    raise HTTPException(status_code=500, detail="Failed to cancel subscription")
            else:
                store.subscription_status = "cancelled"
                await session.commit()
                return {"status": "cancelled"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscription cancellation failed: {e}")
        raise HTTPException(status_code=500, detail="Subscription cancellation failed")


@router.get("/plans")
async def get_available_plans():
    """Get all available subscription plans"""
    
    return {
        "plans": BillingPlanManager.PLANS,
        "currency": "USD",
        "trial_days": 7
    }


async def calculate_usage_stats(session, store_id: int) -> Dict[str, int]:
    """Calculate current usage statistics for a store"""
    
    from sqlalchemy import func
    from models import Product, ProductVariant, Location, Alert
    
    # Count products
    result = await session.execute(
        select(func.count(Product.id)).where(Product.store_id == store_id)
    )
    product_count = result.scalar() or 0
    
    # Count locations  
    result = await session.execute(
        select(func.count(Location.id)).where(Location.store_id == store_id)
    )
    location_count = result.scalar() or 0
    
    # Count alerts
    result = await session.execute(
        select(func.count(Alert.id)).where(Alert.store_id == store_id)
    )
    alert_count = result.scalar() or 0
    
    return {
        "products": product_count,
        "locations": location_count,
        "alerts": alert_count,
        "custom_fields": 0,  # Will implement when custom fields are added
        "workflows": 0       # Will implement when workflows are added
    }


@router.post("/webhook/subscription")
async def handle_subscription_webhook(request: Request):
    """Handle subscription-related webhooks from Shopify"""
    
    try:
        body = await request.body()
        headers = request.headers
        
        # Verify webhook authenticity
        # TODO: Add HMAC verification
        
        import json
        webhook_data = json.loads(body.decode('utf-8'))
        
        logger.info(
            f"Received billing webhook",
            topic=headers.get("X-Shopify-Topic"),
            shop=headers.get("X-Shopify-Shop-Domain")
        )
        
        # Handle different webhook types
        topic = headers.get("X-Shopify-Topic")
        if topic == "app_subscriptions/update":
            await handle_subscription_update(webhook_data)
        elif topic == "app/uninstalled":
            await handle_app_uninstall(webhook_data, headers.get("X-Shopify-Shop-Domain"))
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Billing webhook failed: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


async def handle_subscription_update(webhook_data: Dict[str, Any]):
    """Handle subscription update webhook"""
    # Implementation for handling subscription changes
    pass


async def handle_app_uninstall(webhook_data: Dict[str, Any], shop_domain: str):
    """Handle app uninstall webhook"""
    
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop_domain)
            )
            store = result.scalar_one_or_none()
            
            if store:
                store.subscription_status = "cancelled"
                await session.commit()
                
                logger.info(f"Marked store as uninstalled: {shop_domain}")
                
    except Exception as e:
        logger.error(f"Failed to handle app uninstall: {e}")