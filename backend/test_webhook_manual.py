#!/usr/bin/env python3
"""
Test webhook endpoints manually without ngrok
"""

import requests
import json
import sys
from datetime import datetime

def test_webhook_endpoint():
    """Test webhook endpoint is working"""
    url = "http://localhost:8000/api/v1/webhooks/test"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Webhook test endpoint: {data}")
        return True
        
    except Exception as e:
        print(f"❌ Webhook test failed: {e}")
        return False

def test_product_create_webhook():
    """Test product creation webhook"""
    url = "http://localhost:8000/api/v1/webhooks/products/create"
    
    # Sample product data
    product_data = {
        "id": 7398816999999,
        "title": "Test Webhook Product",
        "handle": "test-webhook-product",
        "product_type": "Test",
        "vendor": "Test Vendor",
        "tags": ["test", "webhook"],
        "status": "active",
        "body_html": "<p>Test product created via webhook</p>",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "published_at": datetime.now().isoformat(),
        "variants": [
            {
                "id": 41234567890123,
                "title": "Default Title",
                "option1": "Default",
                "option2": None,
                "option3": None,
                "sku": "TEST-001",
                "barcode": "123456789",
                "price": "19.99",
                "compare_at_price": "24.99",
                "weight": 0.5,
                "weight_unit": "kg",
                "inventory_quantity": 10,
                "inventory_management": "shopify",
                "inventory_policy": "deny",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Shop-Domain": "inventorysync-dev.myshopify.com",
        "X-Shopify-Hmac-Sha256": "test-signature"
    }
    
    try:
        response = requests.post(url, json=product_data, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Product create webhook: {data}")
        return True
        
    except Exception as e:
        print(f"❌ Product create webhook failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return False

def test_product_update_webhook():
    """Test product update webhook"""
    url = "http://localhost:8000/api/v1/webhooks/products/update"
    
    # Sample product data (updating existing product)
    product_data = {
        "id": 7398816088139,  # Existing product ID
        "title": "Premium Wireless Headphones - Updated",
        "handle": "premium-wireless-headphones-updated",
        "product_type": "Electronics",
        "vendor": "TechCorp",
        "tags": ["electronics", "audio", "wireless", "updated"],
        "status": "active",
        "body_html": "<p>Updated high-quality wireless headphones with noise cancellation</p>",
        "created_at": "2025-07-09T21:00:00Z",
        "updated_at": datetime.now().isoformat(),
        "published_at": "2025-07-09T21:00:00Z",
        "variants": [
            {
                "id": 41234567890001,
                "title": "Black",
                "option1": "Black",
                "option2": None,
                "option3": None,
                "sku": "WH-001-BLK",
                "barcode": "",
                "price": "179.99",  # Updated price
                "compare_at_price": "199.99",
                "weight": 0.8,
                "weight_unit": "kg",
                "inventory_quantity": 45,  # Updated quantity
                "inventory_management": "shopify",
                "inventory_policy": "deny",
                "created_at": "2025-07-09T21:00:00Z",
                "updated_at": datetime.now().isoformat()
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Shop-Domain": "inventorysync-dev.myshopify.com",
        "X-Shopify-Hmac-Sha256": "test-signature"
    }
    
    try:
        response = requests.post(url, json=product_data, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Product update webhook: {data}")
        return True
        
    except Exception as e:
        print(f"❌ Product update webhook failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return False

def test_order_create_webhook():
    """Test order creation webhook"""
    url = "http://localhost:8000/api/v1/webhooks/orders/create"
    
    # Sample order data
    order_data = {
        "id": 4567890123456,
        "name": "#TEST001",
        "email": "customer@example.com",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "line_items": [
            {
                "id": 9876543210,
                "variant_id": 41234567890001,
                "title": "Premium Wireless Headphones",
                "quantity": 2,
                "price": "179.99",
                "sku": "WH-001-BLK",
                "product_id": 7398816088139
            }
        ],
        "total_price": "359.98",
        "subtotal_price": "359.98",
        "financial_status": "paid",
        "fulfillment_status": None
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Shop-Domain": "inventorysync-dev.myshopify.com",
        "X-Shopify-Hmac-Sha256": "test-signature"
    }
    
    try:
        response = requests.post(url, json=order_data, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Order create webhook: {data}")
        return True
        
    except Exception as e:
        print(f"❌ Order create webhook failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return False

def verify_database_changes():
    """Verify webhook changes in database"""
    import sqlite3
    
    conn = sqlite3.connect('inventorysync_dev.db')
    cursor = conn.cursor()
    
    try:
        # Check total products
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        print(f"📊 Total products in database: {product_count}")
        
        # Check recent updates
        cursor.execute("""
            SELECT title, vendor, updated_at 
            FROM products 
            ORDER BY updated_at DESC 
            LIMIT 5
        """)
        recent_products = cursor.fetchall()
        
        print(f"📦 Recent products:")
        for product in recent_products:
            print(f"  - {product[0]} by {product[1]} (updated: {product[2]})")
        
        # Check inventory levels
        cursor.execute("""
            SELECT p.title, pv.title, pv.inventory_quantity
            FROM product_variants pv
            JOIN products p ON pv.product_id = p.id
            WHERE pv.inventory_quantity < 50
            ORDER BY pv.inventory_quantity ASC
        """)
        low_stock = cursor.fetchall()
        
        print(f"📉 Low stock items:")
        for item in low_stock:
            print(f"  - {item[0]} - {item[1]}: {item[2]} units")
        
    finally:
        conn.close()

def main():
    """Main function"""
    print("🔄 Testing webhook endpoints...")
    
    tests = [
        ("Webhook Test Endpoint", test_webhook_endpoint),
        ("Product Create Webhook", test_product_create_webhook),
        ("Product Update Webhook", test_product_update_webhook),
        ("Order Create Webhook", test_order_create_webhook)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Testing {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed > 0:
        print("\n🔍 Verifying database changes...")
        verify_database_changes()
    
    if passed == total:
        print("\n✅ All webhook tests passed!")
        return 0
    else:
        print("\n❌ Some webhook tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())