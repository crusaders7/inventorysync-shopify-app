#!/usr/bin/env python3
"""
Create test products in Shopify store via API
"""

import requests
import json
import sqlite3
import sys
from datetime import datetime

def get_store_access_token(shop_domain: str) -> str:
    """Get access token for store"""
    conn = sqlite3.connect('inventorysync_dev.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT access_token FROM stores WHERE shopify_domain = ?", (shop_domain,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def create_test_product(shop_domain: str, access_token: str, product_data: dict) -> bool:
    """Create a test product in Shopify"""
    url = f"https://{shop_domain}/admin/api/2023-10/products.json"
    
    headers = {
        'X-Shopify-Access-Token': access_token,
        'Content-Type': 'application/json'
    }
    
    payload = {
        "product": product_data
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        created_product = response.json()
        product_id = created_product['product']['id']
        product_title = created_product['product']['title']
        
        print(f"✅ Created product: {product_title} (ID: {product_id})")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating product: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return False

def main():
    """Create test products in Shopify store"""
    shop_domain = "inventorysync-dev.myshopify.com"
    
    # Get access token
    access_token = get_store_access_token(shop_domain)
    if not access_token:
        print(f"❌ No access token found for store: {shop_domain}")
        return 1
    
    print(f"🔄 Creating test products in store: {shop_domain}")
    
    # Test products to create
    test_products = [
        {
            "title": "Premium Wireless Headphones",
            "body_html": "<p>High-quality wireless headphones with noise cancellation</p>",
            "vendor": "TechCorp",
            "product_type": "Electronics",
            "tags": ["electronics", "audio", "wireless"],
            "variants": [
                {
                    "option1": "Black",
                    "price": "199.99",
                    "sku": "WH-001-BLK",
                    "inventory_quantity": 50,
                    "inventory_management": "shopify"
                },
                {
                    "option1": "White", 
                    "price": "199.99",
                    "sku": "WH-001-WHT",
                    "inventory_quantity": 30,
                    "inventory_management": "shopify"
                }
            ],
            "options": [
                {
                    "name": "Color",
                    "values": ["Black", "White"]
                }
            ]
        },
        {
            "title": "Organic Cotton T-Shirt",
            "body_html": "<p>Comfortable organic cotton t-shirt, ethically sourced</p>",
            "vendor": "EcoWear",
            "product_type": "Clothing",
            "tags": ["clothing", "organic", "sustainable"],
            "variants": [
                {
                    "option1": "Small",
                    "option2": "Blue",
                    "price": "29.99",
                    "sku": "TS-001-S-BLU",
                    "inventory_quantity": 25,
                    "inventory_management": "shopify"
                },
                {
                    "option1": "Medium",
                    "option2": "Blue", 
                    "price": "29.99",
                    "sku": "TS-001-M-BLU",
                    "inventory_quantity": 40,
                    "inventory_management": "shopify"
                },
                {
                    "option1": "Large",
                    "option2": "Blue",
                    "price": "29.99", 
                    "sku": "TS-001-L-BLU",
                    "inventory_quantity": 35,
                    "inventory_management": "shopify"
                },
                {
                    "option1": "Small",
                    "option2": "Green",
                    "price": "29.99",
                    "sku": "TS-001-S-GRN",
                    "inventory_quantity": 20,
                    "inventory_management": "shopify"
                }
            ],
            "options": [
                {
                    "name": "Size",
                    "values": ["Small", "Medium", "Large"]
                },
                {
                    "name": "Color", 
                    "values": ["Blue", "Green"]
                }
            ]
        },
        {
            "title": "Stainless Steel Water Bottle",
            "body_html": "<p>Durable stainless steel water bottle, keeps drinks cold for 24 hours</p>",
            "vendor": "HydroLife",
            "product_type": "Accessories",
            "tags": ["accessories", "hydration", "stainless-steel"],
            "variants": [
                {
                    "option1": "500ml",
                    "price": "24.99",
                    "sku": "WB-001-500",
                    "inventory_quantity": 100,
                    "inventory_management": "shopify"
                },
                {
                    "option1": "750ml",
                    "price": "29.99", 
                    "sku": "WB-001-750",
                    "inventory_quantity": 75,
                    "inventory_management": "shopify"
                }
            ],
            "options": [
                {
                    "name": "Size",
                    "values": ["500ml", "750ml"]
                }
            ]
        }
    ]
    
    # Create products
    created_count = 0
    for product_data in test_products:
        if create_test_product(shop_domain, access_token, product_data):
            created_count += 1
    
    print(f"\n✅ Created {created_count}/{len(test_products)} test products successfully!")
    
    if created_count > 0:
        print(f"\n🔄 Now run: python sync_shopify_products.py")
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())