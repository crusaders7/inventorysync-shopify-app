#!/usr/bin/env python3
"""
Fix PostgreSQL database schema - add missing columns
"""

import os
import sys
from sqlalchemy import create_engine, text
from database import engine
from models import Base, Store

def fix_postgres_schema():
    """Add missing columns to PostgreSQL database"""
    
    try:
        # Create connection
        with engine.connect() as conn:
            # Check if shopify_domain column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'stores' 
                AND column_name = 'shopify_domain'
            """))
            
            if not result.fetchone():
                print("Adding shopify_domain column to stores table...")
                
                # Add shopify_domain column as alias for shop_domain
                conn.execute(text("""
                    ALTER TABLE stores 
                    ADD COLUMN IF NOT EXISTS shopify_domain VARCHAR
                """))
                
                # Copy data from shop_domain to shopify_domain
                conn.execute(text("""
                    UPDATE stores 
                    SET shopify_domain = shop_domain
                    WHERE shopify_domain IS NULL
                """))
                
                print("✅ Added shopify_domain column")
            else:
                print("✅ shopify_domain column already exists")
            
            # Ensure we have the test store
            result = conn.execute(text("""
                SELECT id, shop_domain, shopify_domain 
                FROM stores 
                WHERE shop_domain = 'inventorysync-dev.myshopify.com'
                   OR shopify_domain = 'inventorysync-dev.myshopify.com'
            """))
            
            store = result.fetchone()
            if not store:
                print("\nCreating test store...")
                conn.execute(text("""
                    INSERT INTO stores (
                        shopify_store_id, 
                        shop_domain, 
                        shopify_domain,
                        store_name, 
                        access_token,
                        currency,
                        timezone
                    ) VALUES (
                        'inventorysync-dev-store-id',
                        'inventorysync-dev.myshopify.com',
                        'inventorysync-dev.myshopify.com',
                        'InventorySync Dev Store',
                        'test-access-token',
                        'USD',
                        'America/New_York'
                    )
                """))
                print("✅ Created test store")
            else:
                print(f"✅ Store exists: {store}")
                
            conn.commit()
            
        print("\n✅ Database schema fixed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing database schema: {e}")
        return False

if __name__ == "__main__":
    print("Fixing PostgreSQL database schema...")
    success = fix_postgres_schema()
    
    if success:
        print("✅ Database schema fixed successfully")
        sys.exit(0)
    else:
        print("❌ Failed to fix database schema")
        sys.exit(1)
