#!/usr/bin/env python3
"""
Simple inventory update using product variants directly
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

def get_store_id(shop_domain: str) -> int:
    """Get store ID from database"""
    conn = sqlite3.connect('inventorysync_dev.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM stores WHERE shopify_domain = ?", (shop_domain,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def fetch_locations(shop_domain: str, access_token: str) -> list:
    """Fetch locations from Shopify"""
    url = f"https://{shop_domain}/admin/api/2023-10/locations.json"
    
    headers = {
        'X-Shopify-Access-Token': access_token,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        locations = data.get('locations', [])
        
        print(f"✅ Fetched {len(locations)} locations from Shopify")
        return locations
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching locations: {e}")
        return []

def save_locations_to_database(locations: list, store_id: int):
    """Save locations to database"""
    conn = sqlite3.connect('inventorysync_dev.db')
    cursor = conn.cursor()
    
    try:
        locations_saved = 0
        
        for location in locations:
            cursor.execute("""
                INSERT OR REPLACE INTO locations (
                    store_id, shopify_location_id, name, address1, address2,
                    city, province, country, zip, phone, active,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                store_id,
                location['id'],
                location.get('name', ''),
                location.get('address1', ''),
                location.get('address2', ''),
                location.get('city', ''),
                location.get('province', ''),
                location.get('country', ''),
                location.get('zip', ''),
                location.get('phone', ''),
                location.get('active', True),
                location.get('created_at'),
                location.get('updated_at')
            ))
            locations_saved += 1
        
        conn.commit()
        print(f"✅ Saved {locations_saved} locations to database")
        
    except Exception as e:
        print(f"❌ Error saving locations: {e}")
        conn.rollback()
    finally:
        conn.close()

def update_inventory_from_products(shop_domain: str, access_token: str, store_id: int):
    """Update inventory quantities from product data"""
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
        
        print(f"✅ Fetched {len(products)} products for inventory update")
        
        # Update database with current inventory quantities
        conn = sqlite3.connect('inventorysync_dev.db')
        cursor = conn.cursor()
        
        try:
            updated_count = 0
            
            for product in products:
                for variant in product.get('variants', []):
                    shopify_variant_id = str(variant['id'])
                    inventory_quantity = variant.get('inventory_quantity', 0)
                    
                    cursor.execute("""
                        UPDATE product_variants 
                        SET inventory_quantity = ?
                        WHERE shopify_variant_id = ?
                    """, (inventory_quantity, shopify_variant_id))
                    
                    if cursor.rowcount > 0:
                        updated_count += 1
            
            conn.commit()
            print(f"✅ Updated inventory for {updated_count} variants")
            
            # Show current inventory levels
            cursor.execute("""
                SELECT p.title, pv.title, pv.sku, pv.inventory_quantity
                FROM product_variants pv
                JOIN products p ON pv.product_id = p.id
                WHERE p.store_id = ? AND pv.inventory_quantity > 0
                ORDER BY pv.inventory_quantity DESC
            """, (store_id,))
            
            inventory_data = cursor.fetchall()
            
            print(f"\n📦 Current inventory levels:")
            for row in inventory_data:
                product_title, variant_title, sku, quantity = row
                print(f"  {product_title} - {variant_title} ({sku}): {quantity} units")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating inventory: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching products: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Starting simple inventory update...")
    
    shop_domain = "inventorysync-dev.myshopify.com"
    
    # Get store access token
    access_token = get_store_access_token(shop_domain)
    if not access_token:
        print(f"❌ No access token found for store: {shop_domain}")
        return 1
    
    # Get store ID
    store_id = get_store_id(shop_domain)
    if not store_id:
        print(f"❌ Store not found in database: {shop_domain}")
        return 1
    
    print(f"📝 Using store ID: {store_id}")
    
    # Fetch and save locations
    locations = fetch_locations(shop_domain, access_token)
    if locations:
        save_locations_to_database(locations, store_id)
    
    # Update inventory from products
    success = update_inventory_from_products(shop_domain, access_token, store_id)
    
    if success:
        print("\n✅ Inventory update completed successfully!")
        return 0
    else:
        print("\n❌ Inventory update failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())