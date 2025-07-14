"""
Fixed webhook handlers for Shopify product and inventory updates
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import json
import hmac
import hashlib
from datetime import datetime
from typing import Dict, Any
import os
from sqlalchemy.orm import Session
from database import get_db
from models import Store, Product, ProductVariant

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

def verify_webhook_signature(data: bytes, signature: str) -> bool:
    """Verify Shopify webhook signature"""
    webhook_secret = os.getenv("SHOPIFY_WEBHOOK_SECRET", "your-webhook-secret")
    
    computed_signature = hmac.new(
        webhook_secret.encode('utf-8'),
        data,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(computed_signature, signature.replace('sha256=', ''))

@router.post("/products/create")
async def product_create_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle product creation webhook"""
    try:
        # Get raw body and signature
        body = await request.body()
        signature = request.headers.get("X-Shopify-Hmac-Sha256", "")
        
        # Verify signature (skip for development)
        # if not verify_webhook_signature(body, signature):
        #     raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse product data
        product_data = json.loads(body)
        
        # Log the webhook
        print(f"🔔 Product created webhook: {product_data.get('title', 'Unknown')}")
        
        # Get store from shop domain
        shop_domain = request.headers.get("X-Shopify-Shop-Domain")
        if not shop_domain:
            raise HTTPException(status_code=400, detail="Missing shop domain")
        
        # Get store
        store = db.query(Store).filter(Store.shopify_domain == shop_domain).first()
        
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        
        # Check if product already exists
        existing_product = db.query(Product).filter(
            Product.store_id == store.id,
            Product.shopify_product_id == str(product_data['id'])
        ).first()
        
        if existing_product:
            # Update existing product
            existing_product.title = product_data.get('title', '')
            existing_product.handle = product_data.get('handle', '')
            existing_product.product_type = product_data.get('product_type', '')
            existing_product.vendor = product_data.get('vendor', '')
            existing_product.tags = ', '.join(product_data.get('tags', []))
            existing_product.status = product_data.get('status', 'active')
            existing_product.body_html = product_data.get('body_html', '')
            existing_product.updated_at = datetime.utcnow()
            product = existing_product
        else:
            # Create new product
            product = Product(
                store_id=store.id,
                shopify_product_id=str(product_data['id']),
                title=product_data.get('title', ''),
                handle=product_data.get('handle', ''),
                product_type=product_data.get('product_type', ''),
                vendor=product_data.get('vendor', ''),
                tags=', '.join(product_data.get('tags', [])),
                status=product_data.get('status', 'active'),
                body_html=product_data.get('body_html', ''),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(product)
        
        db.flush()  # Get product.id
        
        # Save variants
        for variant_data in product_data.get('variants', []):
            existing_variant = db.query(ProductVariant).filter(
                ProductVariant.shopify_variant_id == str(variant_data['id'])
            ).first()
            
            if existing_variant:
                # Update existing variant
                existing_variant.title = variant_data.get('title', '')
                existing_variant.option1 = variant_data.get('option1')
                existing_variant.option2 = variant_data.get('option2')
                existing_variant.option3 = variant_data.get('option3')
                existing_variant.sku = variant_data.get('sku', '')
                existing_variant.barcode = variant_data.get('barcode', '')
                existing_variant.price = float(variant_data.get('price', 0))
                existing_variant.compare_at_price = float(variant_data.get('compare_at_price', 0)) if variant_data.get('compare_at_price') else None
                existing_variant.weight = float(variant_data.get('weight', 0))
                existing_variant.weight_unit = variant_data.get('weight_unit', 'kg')
                existing_variant.inventory_quantity = int(variant_data.get('inventory_quantity', 0))
                existing_variant.inventory_management = variant_data.get('inventory_management', '')
                existing_variant.inventory_policy = variant_data.get('inventory_policy', 'deny')
                existing_variant.updated_at = datetime.utcnow()
            else:
                # Create new variant
                variant = ProductVariant(
                    product_id=product.id,
                    shopify_variant_id=str(variant_data['id']),
                    title=variant_data.get('title', ''),
                    option1=variant_data.get('option1'),
                    option2=variant_data.get('option2'),
                    option3=variant_data.get('option3'),
                    sku=variant_data.get('sku', ''),
                    barcode=variant_data.get('barcode', ''),
                    price=float(variant_data.get('price', 0)),
                    compare_at_price=float(variant_data.get('compare_at_price', 0)) if variant_data.get('compare_at_price') else None,
                    weight=float(variant_data.get('weight', 0)),
                    weight_unit=variant_data.get('weight_unit', 'kg'),
                    inventory_quantity=int(variant_data.get('inventory_quantity', 0)),
                    inventory_management=variant_data.get('inventory_management', ''),
                    inventory_policy=variant_data.get('inventory_policy', 'deny'),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(variant)
        
        db.commit()
        print(f"✅ Product saved to database: {product_data.get('title')}")
        
        return JSONResponse(content={"status": "success", "message": "Product created"})
        
    except Exception as e:
        db.rollback()
        print(f"❌ Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@router.post("/products/update")
async def product_update_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle product update webhook"""
    return await product_create_webhook(request, db)  # Same logic for create/update

@router.post("/products/delete")
async def product_delete_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle product deletion webhook"""
    try:
        # Get raw body
        body = await request.body()
        product_data = json.loads(body)
        
        # Get store from shop domain
        shop_domain = request.headers.get("X-Shopify-Shop-Domain")
        if not shop_domain:
            raise HTTPException(status_code=400, detail="Missing shop domain")
        
        # Get store
        store = db.query(Store).filter(Store.shopify_domain == shop_domain).first()
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        
        # Delete product
        product = db.query(Product).filter(
            Product.store_id == store.id,
            Product.shopify_product_id == str(product_data['id'])
        ).first()
        
        if product:
            db.delete(product)
            db.commit()
            print(f"✅ Product deleted: {product_data.get('id')}")
        
        return JSONResponse(content={"status": "success", "message": "Product deleted"})
        
    except Exception as e:
        db.rollback()
        print(f"❌ Delete webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@router.post("/app/uninstalled")
async def app_uninstalled_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle app uninstall webhook"""
    try:
        # Get shop domain
        shop_domain = request.headers.get("X-Shopify-Shop-Domain")
        if not shop_domain:
            raise HTTPException(status_code=400, detail="Missing shop domain")
        
        # Mark store as inactive
        store = db.query(Store).filter(Store.shopify_domain == shop_domain).first()
        if store:
            store.is_active = False
            store.uninstalled_at = datetime.utcnow()
            db.commit()
            print(f"✅ App uninstalled for store: {shop_domain}")
        
        return JSONResponse(content={"status": "success", "message": "App uninstalled"})
        
    except Exception as e:
        db.rollback()
        print(f"❌ Uninstall webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")
