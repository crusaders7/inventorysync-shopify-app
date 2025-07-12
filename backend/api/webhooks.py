"""
Real-time webhook handlers for Shopify product and inventory updates
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import json
import sqlite3
import hmac
import hashlib
from datetime import datetime
from typing import Dict, Any
import os

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
async def product_create_webhook(request: Request):
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
        
        # Save to database
        conn = sqlite3.connect('inventorysync_dev.db')
        cursor = conn.cursor()
        
        try:
            # Get store ID
            cursor.execute("SELECT id FROM stores WHERE shopify_domain = ?", (shop_domain,))
            store_result = cursor.fetchone()
            
            if not store_result:
                raise HTTPException(status_code=404, detail="Store not found")
            
            store_id = store_result[0]
            
            # Save product
            cursor.execute("""
                INSERT OR REPLACE INTO products (
                    store_id, shopify_product_id, title, handle, product_type, 
                    vendor, tags, status, body_html, created_at, updated_at, published_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                store_id,
                product_data['id'],
                product_data.get('title', ''),
                product_data.get('handle', ''),
                product_data.get('product_type', ''),
                product_data.get('vendor', ''),
                ', '.join(product_data.get('tags', [])),
                product_data.get('status', 'active'),
                product_data.get('body_html', ''),
                product_data.get('created_at'),
                product_data.get('updated_at'),
                product_data.get('published_at')
            ))
            
            product_db_id = cursor.lastrowid
            
            # Save variants
            for variant in product_data.get('variants', []):
                cursor.execute("""
                    INSERT OR REPLACE INTO product_variants (
                        product_id, shopify_variant_id, title, option1, option2, option3,
                        sku, barcode, price, compare_at_price, weight, weight_unit,
                        inventory_quantity, inventory_management, inventory_policy,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product_db_id,
                    variant['id'],
                    variant.get('title', ''),
                    variant.get('option1'),
                    variant.get('option2'),
                    variant.get('option3'),
                    variant.get('sku', ''),
                    variant.get('barcode', ''),
                    float(variant.get('price', 0)),
                    float(variant.get('compare_at_price', 0)) if variant.get('compare_at_price') else None,
                    float(variant.get('weight', 0)),
                    variant.get('weight_unit', 'kg'),
                    int(variant.get('inventory_quantity', 0)),
                    variant.get('inventory_management', ''),
                    variant.get('inventory_policy', 'deny'),
                    variant.get('created_at'),
                    variant.get('updated_at')
                ))
            
            conn.commit()
            print(f"✅ Product saved to database: {product_data.get('title')}")
            
            return JSONResponse(content={"status": "success", "message": "Product created"})
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error saving product: {e}")
            raise HTTPException(status_code=500, detail="Database error")
        finally:
            conn.close()
            
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@router.post("/products/update")
async def product_update_webhook(request: Request):
    """Handle product update webhook"""
    try:
        # Get raw body and signature
        body = await request.body()
        signature = request.headers.get("X-Shopify-Hmac-Sha256", "")
        
        # Parse product data
        product_data = json.loads(body)
        
        # Log the webhook
        print(f"🔔 Product updated webhook: {product_data.get('title', 'Unknown')}")
        
        # Get store from shop domain
        shop_domain = request.headers.get("X-Shopify-Shop-Domain")
        if not shop_domain:
            raise HTTPException(status_code=400, detail="Missing shop domain")
        
        # Update database
        conn = sqlite3.connect('inventorysync_dev.db')
        cursor = conn.cursor()
        
        try:
            # Get store ID
            cursor.execute("SELECT id FROM stores WHERE shopify_domain = ?", (shop_domain,))
            store_result = cursor.fetchone()
            
            if not store_result:
                raise HTTPException(status_code=404, detail="Store not found")
            
            store_id = store_result[0]
            
            # Update product
            cursor.execute("""
                UPDATE products SET
                    title = ?, handle = ?, product_type = ?, vendor = ?, tags = ?,
                    status = ?, body_html = ?, updated_at = ?, published_at = ?
                WHERE store_id = ? AND shopify_product_id = ?
            """, (
                product_data.get('title', ''),
                product_data.get('handle', ''),
                product_data.get('product_type', ''),
                product_data.get('vendor', ''),
                ', '.join(product_data.get('tags', [])),
                product_data.get('status', 'active'),
                product_data.get('body_html', ''),
                product_data.get('updated_at'),
                product_data.get('published_at'),
                store_id,
                product_data['id']
            ))
            
            # Update variants
            for variant in product_data.get('variants', []):
                cursor.execute("""
                    UPDATE product_variants SET
                        title = ?, option1 = ?, option2 = ?, option3 = ?, sku = ?,
                        barcode = ?, price = ?, compare_at_price = ?, weight = ?,
                        weight_unit = ?, inventory_quantity = ?, inventory_management = ?,
                        inventory_policy = ?, updated_at = ?
                    WHERE shopify_variant_id = ?
                """, (
                    variant.get('title', ''),
                    variant.get('option1'),
                    variant.get('option2'),
                    variant.get('option3'),
                    variant.get('sku', ''),
                    variant.get('barcode', ''),
                    float(variant.get('price', 0)),
                    float(variant.get('compare_at_price', 0)) if variant.get('compare_at_price') else None,
                    float(variant.get('weight', 0)),
                    variant.get('weight_unit', 'kg'),
                    int(variant.get('inventory_quantity', 0)),
                    variant.get('inventory_management', ''),
                    variant.get('inventory_policy', 'deny'),
                    variant.get('updated_at'),
                    variant['id']
                ))
            
            conn.commit()
            print(f"✅ Product updated in database: {product_data.get('title')}")
            
            return JSONResponse(content={"status": "success", "message": "Product updated"})
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error updating product: {e}")
            raise HTTPException(status_code=500, detail="Database error")
        finally:
            conn.close()
            
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@router.post("/products/delete")
async def product_delete_webhook(request: Request):
    """Handle product deletion webhook"""
    try:
        # Get raw body and signature
        body = await request.body()
        signature = request.headers.get("X-Shopify-Hmac-Sha256", "")
        
        # Parse product data
        product_data = json.loads(body)
        
        # Log the webhook
        print(f"🔔 Product deleted webhook: {product_data.get('title', 'Unknown')}")
        
        # Get store from shop domain
        shop_domain = request.headers.get("X-Shopify-Shop-Domain")
        if not shop_domain:
            raise HTTPException(status_code=400, detail="Missing shop domain")
        
        # Delete from database
        conn = sqlite3.connect('inventorysync_dev.db')
        cursor = conn.cursor()
        
        try:
            # Get store ID
            cursor.execute("SELECT id FROM stores WHERE shopify_domain = ?", (shop_domain,))
            store_result = cursor.fetchone()
            
            if not store_result:
                raise HTTPException(status_code=404, detail="Store not found")
            
            store_id = store_result[0]
            
            # Delete product and variants (cascading)
            cursor.execute("""
                DELETE FROM products 
                WHERE store_id = ? AND shopify_product_id = ?
            """, (store_id, product_data['id']))
            
            conn.commit()
            print(f"✅ Product deleted from database: {product_data.get('title')}")
            
            return JSONResponse(content={"status": "success", "message": "Product deleted"})
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error deleting product: {e}")
            raise HTTPException(status_code=500, detail="Database error")
        finally:
            conn.close()
            
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@router.post("/orders/create")
async def order_create_webhook(request: Request):
    """Handle order creation webhook for inventory updates"""
    try:
        # Get raw body and signature
        body = await request.body()
        signature = request.headers.get("X-Shopify-Hmac-Sha256", "")
        
        # Parse order data
        order_data = json.loads(body)
        
        # Log the webhook
        print(f"🔔 Order created webhook: {order_data.get('name', 'Unknown')}")
        
        # Get store from shop domain
        shop_domain = request.headers.get("X-Shopify-Shop-Domain")
        if not shop_domain:
            raise HTTPException(status_code=400, detail="Missing shop domain")
        
        # Update inventory quantities
        conn = sqlite3.connect('inventorysync_dev.db')
        cursor = conn.cursor()
        
        try:
            # Get store ID
            cursor.execute("SELECT id FROM stores WHERE shopify_domain = ?", (shop_domain,))
            store_result = cursor.fetchone()
            
            if not store_result:
                raise HTTPException(status_code=404, detail="Store not found")
            
            store_id = store_result[0]
            
            # Update inventory for each line item
            for line_item in order_data.get('line_items', []):
                variant_id = line_item.get('variant_id')
                quantity = line_item.get('quantity', 0)
                
                if variant_id and quantity > 0:
                    cursor.execute("""
                        UPDATE product_variants 
                        SET inventory_quantity = inventory_quantity - ?
                        WHERE shopify_variant_id = ?
                    """, (quantity, str(variant_id)))
            
            conn.commit()
            print(f"✅ Inventory updated for order: {order_data.get('name')}")
            
            return JSONResponse(content={"status": "success", "message": "Order processed"})
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error processing order: {e}")
            raise HTTPException(status_code=500, detail="Database error")
        finally:
            conn.close()
            
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@router.get("/test")
async def test_webhook_endpoint():
    """Test webhook endpoint"""
    return JSONResponse(content={
        "status": "success",
        "message": "Webhook endpoint is working",
        "timestamp": datetime.now().isoformat()
    })
