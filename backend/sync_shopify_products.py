#!/usr/bin/env python3
"""
Sync products from Shopify to local database
"""

import requests
import json
import sqlite3
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

def get_store_access_token(shop_domain: str) -> Optional[str]:
    """Get access token for a store"""
    conn = sqlite3.connect('inventorysync_dev.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT access_token FROM stores WHERE shopify_domain = ?", (shop_domain,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def fetch_shopify_products(shop_domain: str, access_token: str) -> List[Dict]:
    """Fetch products from Shopify API"""
    url = f"https://{shop_domain}/admin/api/2023-10/products.json"
    
    headers = {
        'X-Shopify-Access-Token': access_token,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        products = data.get('products', [])
        
        print(f"✅ Fetched {len(products)} products from Shopify")
        return products
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching products: {e}")
        return []

def create_products_table():
    """Create products table if it doesn't exist"""
    conn = sqlite3.connect('inventorysync_dev.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                store_id INTEGER,
                shopify_product_id TEXT,
                title TEXT,
                handle TEXT,
                product_type TEXT,
                vendor TEXT,
                tags TEXT,
                status TEXT,
                body_html TEXT,
                created_at DATETIME,
                updated_at DATETIME,
                published_at DATETIME,
                FOREIGN KEY (store_id) REFERENCES stores (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_variants (
                id INTEGER PRIMARY KEY,
                product_id INTEGER,
                shopify_variant_id TEXT,
                title TEXT,
                option1 TEXT,
                option2 TEXT,
                option3 TEXT,
                sku TEXT,
                barcode TEXT,
                price REAL,
                compare_at_price REAL,
                weight REAL,
                weight_unit TEXT,
                inventory_quantity INTEGER,
                inventory_management TEXT,
                inventory_policy TEXT,
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        """)
        
        conn.commit()
        print("✅ Products tables created/verified")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        conn.rollback()
    finally:
        conn.close()

def save_products_to_database(products: List[Dict], store_id: int):
    """Save products to local database"""
    conn = sqlite3.connect('inventorysync_dev.db')
    cursor = conn.cursor()
    
    try:
        products_saved = 0
        variants_saved = 0
        
        for product in products:
            # Save product
            cursor.execute("""
                INSERT OR REPLACE INTO products (
                    store_id, shopify_product_id, title, handle, product_type, 
                    vendor, tags, status, body_html, created_at, updated_at, published_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                store_id,
                product['id'],
                product.get('title', ''),
                product.get('handle', ''),
                product.get('product_type', ''),
                product.get('vendor', ''),
                ', '.join(product.get('tags', [])),
                product.get('status', 'active'),
                product.get('body_html', ''),
                product.get('created_at'),
                product.get('updated_at'),
                product.get('published_at')
            ))
            
            product_db_id = cursor.lastrowid
            products_saved += 1
            
            # Save variants
            for variant in product.get('variants', []):
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
                variants_saved += 1
        
        conn.commit()
        print(f"✅ Saved {products_saved} products and {variants_saved} variants to database")
        
    except Exception as e:
        print(f"❌ Error saving products: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_store_id(shop_domain: str) -> Optional[int]:
    """Get store ID from database"""
    conn = sqlite3.connect('inventorysync_dev.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM stores WHERE shopify_domain = ?", (shop_domain,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def sync_products_for_store(shop_domain: str) -> bool:
    """Sync products for a specific store"""
    print(f"🔄 Syncing products for store: {shop_domain}")
    
    # Get store access token
    access_token = get_store_access_token(shop_domain)
    if not access_token:
        print(f"❌ No access token found for store: {shop_domain}")
        return False
    
    # Get store ID
    store_id = get_store_id(shop_domain)
    if not store_id:
        print(f"❌ Store not found in database: {shop_domain}")
        return False
    
    print(f"📝 Using store ID: {store_id}")
    
    # Create tables if needed
    create_products_table()
    
    # Fetch products from Shopify
    products = fetch_shopify_products(shop_domain, access_token)
    if not products:
        print("❌ No products fetched from Shopify")
        return False
    
    # Save to database
    save_products_to_database(products, store_id)
    
    # Verify saved products
    conn = sqlite3.connect('inventorysync_dev.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM products WHERE store_id = ?", (store_id,))
        product_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM product_variants WHERE product_id IN (SELECT id FROM products WHERE store_id = ?)", (store_id,))
        variant_count = cursor.fetchone()[0]
        
        print(f"✅ Total products in database: {product_count}")
        print(f"✅ Total variants in database: {variant_count}")
        
        # Show sample products
        cursor.execute("SELECT title, product_type, vendor FROM products WHERE store_id = ? LIMIT 5", (store_id,))
        sample_products = cursor.fetchall()
        
        print(f"\n📦 Sample products:")
        for product in sample_products:
            print(f"  - {product[0]} ({product[1]}) by {product[2]}")
        
        return True
        
    finally:
        conn.close()

def main():
    """Main function"""
    print("🚀 Starting Shopify product sync...")
    
    # Use our development store
    shop_domain = "inventorysync-dev.myshopify.com"
    
    success = sync_products_for_store(shop_domain)
    
    if success:
        print("\n✅ Product sync completed successfully!")
        return 0
    else:
        print("\n❌ Product sync failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())