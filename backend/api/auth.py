"""
Shopify Authentication API Endpoints
Handles OAuth flow for InventorySync
"""

from fastapi import APIRouter, HTTPException, Query, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from urllib.parse import urlencode, parse_qs
from typing import Optional, Dict
from datetime import datetime, timedelta
import logging
import os
import secrets
import hashlib
import hmac
import base64

# Import our utilities
from utils.validation import ShopDomainValidator, APIKeyValidator
from utils.logging import logger
from utils.exceptions import validation_error, unauthorized_error
from database import AsyncSessionLocal
from models import Store, Location
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.post("/dev-setup")
async def dev_setup(shop: str = "inventorysync-dev.myshopify.com"):
    """Development endpoint to bypass OAuth for testing"""
    try:
        from sqlalchemy.orm import sessionmaker
        from database import engine
        
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if store already exists
        existing_store = session.query(Store).filter(Store.shopify_domain == shop).first()
        if existing_store:
            session.close()
            return {"message": "Store already exists", "shop": shop}
        
        # Create a mock store entry for development
        new_store = Store(
            shopify_store_id="12345",  # Mock store ID
            shop_domain=shop,
            store_name="InventorySync Dev Store",
            access_token=os.getenv("DEV_ACCESS_TOKEN", "dev_token_123")  # Mock token for development
        )
        
        session.add(new_store)
        session.commit()
        session.close()
        
        logger.info(f"Dev store created: {shop}")
        
        return {
            "message": "Development store created successfully", 
            "shop": shop,
            "redirect": f"{settings.frontend_url}/?authenticated=true"
        }
        
    except Exception as e:
        logger.error(f"Dev setup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Setup failed: {str(e)}")


@router.get("/install")
async def install_app(
    shop: str = Query(..., description="Shop domain (e.g., mystore.myshopify.com)"),
    request: Request = None
):
    """
    Initiate Shopify app installation
    Redirects user to Shopify OAuth authorization with enhanced security
    """
    try:
        # Validate shop domain
        shop_domain = ShopDomainValidator.validate(shop)
        
        # Get credentials from settings
        api_key = settings.shopify_api_key
        if not api_key:
            logger.error("Shopify API key not configured")
            raise HTTPException(status_code=500, detail="Application not properly configured")
        
        # Validate API key format
        try:
            APIKeyValidator.validate_api_key(api_key)
        except ValueError as e:
            logger.error(f"Invalid API key format: {e}")
            raise HTTPException(status_code=500, detail="Invalid API configuration")
        
        # Generate secure state parameter for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store state in session/cache (in production, use Redis)
        # For now, we'll use a simple approach
        
        # Required Shopify scopes for inventory management
        scopes = [
            "read_products",
            "write_products",
            "read_inventory",
            "write_inventory",
            "read_orders",
            "write_orders",
            "read_customers"
        ]
        
        redirect_uri = f"{settings.app_url if hasattr(settings, 'app_url') else 'http://localhost:8000'}/api/v1/auth/callback"
        
        # Build authorization URL with enhanced security
        params = {
            "client_id": api_key,
            "scope": ",".join(scopes),
            "redirect_uri": redirect_uri,
            "state": state
        }
        
        shop_name = shop_domain.replace('.myshopify.com', '')
        auth_url = f"https://{shop_name}.myshopify.com/admin/oauth/authorize?{urlencode(params)}"
        
        # Log installation attempt
        logger.info(
            f"Shop installation initiated",
            shop_domain=shop_domain,
            client_ip=request.client.host if request and request.client else None,
            state=state[:8] + "...",  # Log partial state for debugging
            scopes=scopes
        )
        
        # In production, store state in Redis with expiration
        # redis.setex(f"oauth_state:{state}", 300, shop_domain)  # 5 minute expiry
        
        return RedirectResponse(url=auth_url)
        
    except ValueError as e:
        logger.warning(f"Validation error in install: {e}", shop=shop)
        raise validation_error(str(e))
    except Exception as e:
        logger.error(f"Install error: {str(e)}", shop=shop, exc_info=e)
        raise HTTPException(status_code=500, detail="Installation failed")


@router.get("/callback")
async def auth_callback(
    shop: str = Query(...),
    code: str = Query(...),
    state: Optional[str] = Query(None),
    hmac: Optional[str] = Query(None),
    timestamp: Optional[str] = Query(None),
    request: Request = None
):
    """
    Handle Shopify OAuth callback with enhanced security
    Exchange authorization code for access token
    """
    try:
        # Validate shop domain
        shop_domain = ShopDomainValidator.validate(shop)
        
        # Verify state parameter (CSRF protection)
        if not state:
            logger.warning(f"Missing state parameter in callback", shop=shop_domain)
            raise unauthorized_error("Invalid request - missing state parameter")
        
        # In production, verify state from Redis
        # stored_shop = redis.get(f"oauth_state:{state}")
        # if not stored_shop or stored_shop.decode() != shop_domain:
        #     raise unauthorized_error("Invalid state parameter")
        
        # Verify request authenticity using HMAC
        if hmac and settings.shopify_api_secret:
            query_params = dict(request.query_params)
            if not verify_shopify_hmac(query_params, settings.shopify_api_secret):
                logger.warning(f"HMAC verification failed", shop=shop_domain)
                raise unauthorized_error("Request verification failed")
        
        logger.info(
            f"Processing OAuth callback",
            shop_domain=shop_domain,
            state=state[:8] + "...",
            has_hmac=bool(hmac)
        )
        
        # Exchange code for access token
        from shopify_client import ShopifyAuth, ShopifyClient
        
        auth = ShopifyAuth()
        access_token = await auth.exchange_code_for_token(shop_domain, code)
        
        logger.info(f"Successfully obtained access token", shop_domain=shop_domain)
        
        # Get shop and location info from Shopify
        client = ShopifyClient(shop_domain, access_token)
        shop_info = await client.get_shop_info()
        locations_info = await client.get_locations()
        
        # Store in database using async session
        async with AsyncSessionLocal() as session:
            try:
                # Check if store already exists
                from sqlalchemy import select
                result = await session.execute(
                    select(Store).where(Store.shopify_domain == shop_domain)
                )
                existing_store = result.scalar_one_or_none()
                
                if existing_store:
                    # Update existing store
                    existing_store.access_token = access_token
                    existing_store.store_name = shop_info.get("shop", {}).get("name", shop_domain)
                    existing_store.currency = shop_info.get("shop", {}).get("currency", "USD")
                    existing_store.timezone = shop_info.get("shop", {}).get("iana_timezone", "UTC")
                    
                    logger.info(f"Updated existing store", shop_domain=shop_domain)
                    store = existing_store
                else:
                    # Create new store
                    shop_data = shop_info.get("shop", {})
                    store = Store(
                        shopify_store_id=str(shop_data.get("id", "unknown")),
                        shop_domain=shop_domain,
                        store_name=shop_data.get("name", shop_domain),
                        currency=shop_data.get("currency", "USD"),
                        timezone=shop_data.get("iana_timezone", "UTC"),
                        subscription_plan="starter",
                        subscription_status="active",
                        access_token=access_token
                    )
                    session.add(store)
                    await session.flush()  # Get the store.id
                    
                    logger.info(f"Created new store", shop_domain=shop_domain)
                
                # Create/update locations
                for location_data in locations_info.get("locations", []):
                    result = await session.execute(
                        select(Location).where(
                            Location.store_id == store.id,
                            Location.shopify_location_id == str(location_data["id"])
                        )
                    )
                    existing_location = result.scalar_one_or_none()
                    
                    if not existing_location:
                        location = Location(
                            store_id=store.id,
                            shopify_location_id=str(location_data["id"]),
                            name=location_data.get("name", "Unknown Location"),
                            address=location_data.get("address1", ""),
                            city=location_data.get("city", ""),
                            country=location_data.get("country_code", ""),
                            is_active=location_data.get("active", True),
                            manages_inventory=True
                        )
                        session.add(location)
                
                await session.commit()
                
                # Set up mandatory webhooks
                await setup_mandatory_webhooks(shop_domain, access_token)
                
                # Log successful authentication
                logger.info(
                    f"Authentication completed successfully",
                    shop_domain=shop_domain,
                    store_id=store.id,
                    locations_count=len(locations_info.get("locations", []))
                )
                
            except Exception as e:
                await session.rollback()
                raise e
        
        # Clean up state from cache
        # redis.delete(f"oauth_state:{state}")
        
        # Check if billing is needed
        if store.subscription_status in ["trial", "pending"] and not store.shopify_charge_id:
            # Redirect to billing setup
            billing_url = f"{settings.frontend_url if hasattr(settings, 'frontend_url') else 'http://localhost:3000'}/?shop={shop_domain}&setup=billing"
            return RedirectResponse(url=billing_url)
        else:
            # Redirect to app dashboard with success
            frontend_url = settings.frontend_url if hasattr(settings, 'frontend_url') else "http://localhost:3000"
            dashboard_url = f"{frontend_url}/?shop={shop_domain}&authenticated=true&setup=complete"
            return RedirectResponse(url=dashboard_url)
        
    except ValueError as e:
        logger.warning(f"Validation error in callback: {e}", shop=shop)
        error_url = f"{settings.frontend_url if hasattr(settings, 'frontend_url') else 'http://localhost:3000'}/?error=validation_failed"
        return RedirectResponse(url=error_url)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Callback error: {str(e)}", shop=shop, exc_info=e)
        error_url = f"{settings.frontend_url if hasattr(settings, 'frontend_url') else 'http://localhost:3000'}/?error=authentication_failed"
        return RedirectResponse(url=error_url)


def verify_shopify_hmac(query_params: Dict[str, str], api_secret: str) -> bool:
    """Verify Shopify HMAC signature"""
    if 'hmac' not in query_params:
        return False
    
    hmac_to_verify = query_params.pop('hmac')
    
    # Sort parameters and create query string
    sorted_params = sorted(query_params.items())
    query_string = "&".join([f"{k}={v}" for k, v in sorted_params])
    
    calculated_hmac = hmac.new(
        api_secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(calculated_hmac, hmac_to_verify)


@router.get("/status")
async def auth_status():
    """
    Check authentication configuration and system status
    """
    try:
        api_key = settings.shopify_api_key
        api_secret = settings.shopify_api_secret
        
        # Check database connectivity
        db_healthy = False
        store_count = 0
        try:
            async with AsyncSessionLocal() as session:
                from sqlalchemy import select, func
                result = await session.execute(select(func.count(Store.id)))
                store_count = result.scalar()
                db_healthy = True
        except Exception as e:
            logger.error(f"Database check failed in auth status: {e}")
        
        status = {
            "configured": bool(api_key and api_secret),
            "api_key_set": bool(api_key),
            "api_secret_set": bool(api_secret),
            "database_healthy": db_healthy,
            "connected_stores": store_count,
            "app_url": getattr(settings, 'app_url', 'http://localhost:8000'),
            "frontend_url": getattr(settings, 'frontend_url', 'http://localhost:3000'),
            "environment": getattr(settings, 'environment', 'development'),
            "timestamp": datetime.now().isoformat()
        }
        
        # Validate API key format if present
        if api_key:
            try:
                APIKeyValidator.validate_api_key(api_key)
                status["api_key_valid"] = True
            except ValueError:
                status["api_key_valid"] = False
                status["configured"] = False
        
        logger.info("Auth status check completed", **status)
        return status
        
    except Exception as e:
        logger.error(f"Auth status check failed: {e}", exc_info=e)
        return {
            "configured": False,
            "error": "Status check failed",
            "timestamp": datetime.now().isoformat()
        }


@router.post("/webhook")
async def shopify_webhook(
    request: Request,
    x_shopify_topic: str = None,
    x_shopify_hmac_sha256: str = None,
    x_shopify_shop_domain: str = None
):
    """
    Handle Shopify webhooks for real-time updates
    """
    try:
        # Get headers
        topic = request.headers.get("X-Shopify-Topic")
        hmac_header = request.headers.get("X-Shopify-Hmac-Sha256")
        shop_domain = request.headers.get("X-Shopify-Shop-Domain")
        
        if not all([topic, hmac_header, shop_domain]):
            logger.warning("Missing required webhook headers")
            raise HTTPException(status_code=400, detail="Missing required headers")
        
        # Read request body
        body = await request.body()
        
        # Verify webhook authenticity
        if settings.shopify_webhook_secret:
            calculated_hmac = base64.b64encode(
                hmac.new(
                    settings.shopify_webhook_secret.encode('utf-8'),
                    body,
                    hashlib.sha256
                ).digest()
            ).decode()
            
            if not hmac.compare_digest(calculated_hmac, hmac_header):
                logger.warning(
                    f"Webhook HMAC verification failed",
                    shop_domain=shop_domain,
                    topic=topic
                )
                raise HTTPException(status_code=401, detail="Unauthorized")
        
        # Parse webhook data
        import json
        webhook_data = json.loads(body.decode('utf-8'))
        
        logger.info(
            f"Received webhook",
            shop_domain=shop_domain,
            topic=topic,
            webhook_id=webhook_data.get('id')
        )
        
        # Process webhook based on topic
        if topic == "products/create":
            await handle_product_created(shop_domain, webhook_data)
        elif topic == "products/update":
            await handle_product_updated(shop_domain, webhook_data)
        elif topic == "inventory_levels/update":
            await handle_inventory_updated(shop_domain, webhook_data)
        elif topic == "app/uninstalled":
            await handle_app_uninstalled(shop_domain, webhook_data)
        elif topic == "customers/data_request":
            await handle_customer_data_request(shop_domain, webhook_data)
        elif topic == "customers/redact":
            await handle_customer_redact(shop_domain, webhook_data)
        elif topic == "shop/redact":
            await handle_shop_redact(shop_domain, webhook_data)
        else:
            logger.info(f"Unhandled webhook topic: {topic}")
        
        return JSONResponse(
            status_code=200,
            content={"status": "received", "topic": topic}
        )
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}", exc_info=e)
        raise HTTPException(status_code=500, detail="Webhook processing failed")


# Webhook handlers
async def handle_product_created(shop_domain: str, product_data: dict):
    """Handle product creation webhook"""
    logger.info(f"Product created", shop_domain=shop_domain, product_id=product_data.get('id'))
    # TODO: Sync new product to local database


async def handle_product_updated(shop_domain: str, product_data: dict):
    """Handle product update webhook"""
    logger.info(f"Product updated", shop_domain=shop_domain, product_id=product_data.get('id'))
    # TODO: Update product in local database


async def handle_inventory_updated(shop_domain: str, inventory_data: dict):
    """Handle inventory level update webhook"""
    logger.info(f"Inventory updated", shop_domain=shop_domain, inventory_item_id=inventory_data.get('inventory_item_id'))
    # TODO: Update inventory in local database


async def handle_app_uninstalled(shop_domain: str, uninstall_data: dict):
    """Handle app uninstallation webhook"""
    logger.warning(f"App uninstalled", shop_domain=shop_domain)
    
    try:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop_domain)
            )
            store = result.scalar_one_or_none()
            
            if store:
                store.subscription_status = "cancelled"
                await session.commit()
                logger.info(f"Store marked as uninstalled", shop_domain=shop_domain)
                
    except Exception as e:
        logger.error(f"Failed to handle app uninstall: {e}", shop_domain=shop_domain)


async def handle_customer_data_request(shop_domain: str, request_data: dict):
    """Handle customer data request webhook (GDPR compliance)"""
    customer_id = request_data.get("customer", {}).get("id")
    customer_email = request_data.get("customer", {}).get("email")
    
    logger.info(
        f"Customer data request received",
        shop_domain=shop_domain,
        customer_id=customer_id,
        customer_email=customer_email
    )
    
    # TODO: Implement customer data export
    # For GDPR compliance, you need to:
    # 1. Identify all customer data in your system
    # 2. Export it in a machine-readable format
    # 3. Send it to the customer within 30 days


async def handle_customer_redact(shop_domain: str, redact_data: dict):
    """Handle customer redaction webhook (GDPR compliance)"""
    customer_id = redact_data.get("customer", {}).get("id")
    customer_email = redact_data.get("customer", {}).get("email")
    
    logger.info(
        f"Customer redaction request received",
        shop_domain=shop_domain,
        customer_id=customer_id,
        customer_email=customer_email
    )
    
    # TODO: Implement customer data deletion
    # For GDPR compliance, you need to:
    # 1. Identify all customer data in your system
    # 2. Permanently delete it
    # 3. Confirm deletion


async def handle_shop_redact(shop_domain: str, redact_data: dict):
    """Handle shop redaction webhook (GDPR compliance)"""
    shop_id = redact_data.get("shop_id")
    
    logger.info(
        f"Shop redaction request received",
        shop_domain=shop_domain,
        shop_id=shop_id
    )
    
    try:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Store).where(Store.shopify_domain == shop_domain)
            )
            store = result.scalar_one_or_none()
            
            if store:
                # Mark for deletion after 48 hours (Shopify requirement)
                from datetime import datetime, timedelta
                store.deletion_scheduled_at = datetime.now() + timedelta(hours=48)
                await session.commit()
                
                logger.info(f"Shop marked for deletion", shop_domain=shop_domain)
                
    except Exception as e:
        logger.error(f"Failed to handle shop redact: {e}", shop_domain=shop_domain)


async def setup_mandatory_webhooks(shop_domain: str, access_token: str):
    """Set up mandatory webhooks required by Shopify"""
    
    webhooks = [
        {
            "webhook": {
                "topic": "app/uninstalled",
                "address": f"{settings.app_url}/api/v1/auth/webhook",
                "format": "json"
            }
        },
        {
            "webhook": {
                "topic": "customers/data_request",
                "address": f"{settings.app_url}/api/v1/auth/webhook",
                "format": "json"
            }
        },
        {
            "webhook": {
                "topic": "customers/redact",
                "address": f"{settings.app_url}/api/v1/auth/webhook",
                "format": "json"
            }
        },
        {
            "webhook": {
                "topic": "shop/redact",
                "address": f"{settings.app_url}/api/v1/auth/webhook",
                "format": "json"
            }
        }
    ]
    
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }
    
    import httpx
    
    for webhook_config in webhooks:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://{shop_domain}/admin/api/2024-01/webhooks.json",
                    headers=headers,
                    json=webhook_config,
                    timeout=30.0
                )
                
                if response.status_code == 201:
                    webhook_data = response.json()
                    logger.info(
                        f"Created webhook: {webhook_config['webhook']['topic']}",
                        shop_domain=shop_domain,
                        webhook_id=webhook_data["webhook"]["id"]
                    )
                elif response.status_code == 422:
                    # Webhook might already exist
                    logger.info(
                        f"Webhook already exists: {webhook_config['webhook']['topic']}",
                        shop_domain=shop_domain
                    )
                else:
                    logger.warning(
                        f"Failed to create webhook: {webhook_config['webhook']['topic']}",
                        shop_domain=shop_domain,
                        status_code=response.status_code,
                        response=response.text
                    )
                    
        except Exception as e:
            logger.error(
                f"Error creating webhook: {webhook_config['webhook']['topic']}",
                shop_domain=shop_domain,
                exc_info=e
            )