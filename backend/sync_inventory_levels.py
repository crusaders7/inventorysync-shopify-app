#!/usr/bin/env python3
"""
Sync inventory levels from Shopify to local database
"""

import requests
import json
import sqlite3
import sys
from datetime import datetime
from typing import Dict, List, Optional

def get_store_access_token(shop_domain: str) -> Optional[str]:
    """Get access token for store"""
    conn = sqlite3.connect('inventorysync_dev.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT access_token FROM stores WHERE shopify_domain = ?", (shop_domain,))
        result = cursor.fetchone()
        return result[0] if result else None
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

def fetch_inventory_levels(shop_domain: str, access_token: str) -> List[Dict]:
    """Fetch inventory levels from Shopify"""
    url = f"https://{shop_domain}/admin/api/2023-10/inventory_levels.json"
    
    headers = {
        'X-Shopify-Access-Token': access_token,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        inventory_levels = data.get('inventory_levels', [])
        
        print(f"✅ Fetched {len(inventory_levels)} inventory levels from Shopify")
        return inventory_levels
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching inventory levels: {e}")
        return []

def fetch_locations(shop_domain: str, access_token: str) -> List[Dict]:
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

def create_inventory_tables():
    """Create inventory and location tables"""
    conn = sqlite3.connect('inventorysync_dev.db')
    cursor = conn.cursor()
    
    try:
        # Create locations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY,
                store_id INTEGER,
                shopify_location_id TEXT,
                name TEXT,
                address1 TEXT,
                address2 TEXT,
                city TEXT,
                province TEXT,
                country TEXT,
                zip TEXT,
                phone TEXT,
                active BOOLEAN,
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY (store_id) REFERENCES stores (id)
            )
        """)
        
        # Create inventory items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_items (
                id INTEGER PRIMARY KEY,
                store_id INTEGER,
                shopify_inventory_item_id TEXT,
                sku TEXT,
                cost REAL,
                tracked BOOLEAN,
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY (store_id) REFERENCES stores (id)
            )
        """)
        
        # Create inventory levels table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_levels (
                id INTEGER PRIMARY KEY,
                inventory_item_id INTEGER,
                location_id INTEGER,
                available INTEGER,
                updated_at DATETIME,
                FOREIGN KEY (inventory_item_id) REFERENCES inventory_items (id),
                FOREIGN KEY (location_id) REFERENCES locations (id)
            )
        """)
        
        conn.commit()
        print("✅ Inventory tables created/verified")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        conn.rollback()
    finally:
        conn.close()

def save_locations_to_database(locations: List[Dict], store_id: int):
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

def get_variant_inventory_items(shop_domain: str, access_token: str) -> Dict[str, str]:
    """Get inventory item IDs for all variants"""
    conn = sqlite3.connect('inventorysync_dev.db')
    cursor = conn.cursor()
    
    try:
        # Get all variants from database
        cursor.execute("SELECT shopify_variant_id FROM product_variants")
        variant_ids = [row[0] for row in cursor.fetchall()]
        
        inventory_items = {}
        
        # Fetch inventory item IDs for each variant
        for variant_id in variant_ids:
            url = f"https://{shop_domain}/admin/api/2023-10/variants/{variant_id}.json"
            
            headers = {
                'X-Shopify-Access-Token': access_token,
                'Content-Type': 'application/json'
            }
            
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                variant = data.get('variant', {})
                inventory_item_id = variant.get('inventory_item_id')
                
                if inventory_item_id:
                    inventory_items[variant_id] = inventory_item_id
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Error fetching variant {variant_id}: {e}")
                continue
        
        print(f"✅ Retrieved inventory item IDs for {len(inventory_items)} variants")
        return inventory_items
        
    finally:
        conn.close()

def sync_inventory_for_store(shop_domain: str) -> bool:
    """Sync inventory for a specific store"""
    print(f"🔄 Syncing inventory for store: {shop_domain}")
    
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
    create_inventory_tables()
    
    # Fetch and save locations
    locations = fetch_locations(shop_domain, access_token)
    if locations:
        save_locations_to_database(locations, store_id)
    
    # Fetch inventory levels
    inventory_levels = fetch_inventory_levels(shop_domain, access_token)
    if not inventory_levels:
        print("❌ No inventory levels fetched from Shopify")
        return False
    
    # Update variant inventory quantities in database
    conn = sqlite3.connect('inventorysync_dev.db')
    cursor = conn.cursor()
    
    try:
        updated_count = 0
        
        # Group inventory levels by inventory item
        inventory_totals = {}
        for level in inventory_levels:
            item_id = level['inventory_item_id']
            available = level['available']
            
            if item_id not in inventory_totals:
                inventory_totals[item_id] = 0
            inventory_totals[item_id] += available
        
        # Update variant quantities
        for item_id, total_quantity in inventory_totals.items():
            cursor.execute("""
                UPDATE product_variants 
                SET inventory_quantity = ?
                WHERE shopify_variant_id IN (
                    SELECT shopify_variant_id FROM product_variants v
                    JOIN products p ON v.product_id = p.id
                    WHERE p.store_id = ?
                )
            """, (total_quantity, store_id))
            
            if cursor.rowcount > 0:
                updated_count += cursor.rowcount
        
        conn.commit()
        print(f"✅ Updated inventory quantities for {updated_count} variants")
        
        # Verify inventory data
        cursor.execute("""
            SELECT pv.sku, pv.title, pv.inventory_quantity, p.title
            FROM product_variants pv
            JOIN products p ON pv.product_id = p.id
            WHERE p.store_id = ? AND pv.inventory_quantity > 0
            ORDER BY pv.inventory_quantity DESC
            LIMIT 10
        """, (store_id,))
        
        inventory_data = cursor.fetchall()
        
        print(f"\n📦 Inventory levels (top 10):")
        for row in inventory_data:
            sku, variant_title, quantity, product_title = row
            print(f"  {product_title} - {variant_title} ({sku}): {quantity} units")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating inventory: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """Main function"""
    print("🚀 Starting inventory sync...")
    
    # Use our development store
    shop_domain = "inventorysync-dev.myshopify.com"
    
    success = sync_inventory_for_store(shop_domain)
    
    if success:
        print("\n✅ Inventory sync completed successfully!")
        return 0
    else:
        print("\n❌ Inventory sync failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())