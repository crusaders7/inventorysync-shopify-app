#!/usr/bin/env python3
"""
Create a test store in the database for development
"""

import psycopg2
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://inventorysync:devpassword123@localhost:5432/inventorysync_dev')

def create_test_store():
    """Create a test store for development"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    try:
        # Check if test store already exists
        cur.execute("""
            SELECT id FROM stores 
            WHERE shopify_domain = 'inventorysync-dev.myshopify.com'
        """)
        existing = cur.fetchone()
        
        if existing:
            print("✅ Test store already exists!")
        else:
            # Create test store
            cur.execute("""
                INSERT INTO stores (
                    shopify_store_id,
                    shop_domain,
                    store_name,
                    shopify_domain,
                    shop_name,
                    email,
                    access_token,
                    currency,
                    timezone,
                    subscription_plan,
                    subscription_status,
                    trial_ends_at,
                    created_at,
                    updated_at
                ) VALUES (
                    'test-store-123',
                    'inventorysync-dev.myshopify.com',
                    'InventorySync Test Store',
                    'inventorysync-dev.myshopify.com',
                    'InventorySync Test Store',
                    'test@inventorysync.com',
                    'test-access-token-development-only',
                    'USD',
                    'America/New_York',
                    'starter',
                    'trial',
                    %s,
                    NOW(),
                    NOW()
                )
            """, (datetime.now() + timedelta(days=14),))
            
            conn.commit()
            print("✅ Test store created successfully!")
        
        # Show store details
        cur.execute("""
            SELECT id, shopify_domain, shop_name, subscription_status, trial_ends_at
            FROM stores 
            WHERE shopify_domain = 'inventorysync-dev.myshopify.com'
        """)
        store = cur.fetchone()
        
        print("\nTest Store Details:")
        print(f"  ID: {store[0]}")
        print(f"  Domain: {store[1]}")
        print(f"  Name: {store[2]}")
        print(f"  Status: {store[3]}")
        print(f"  Trial Ends: {store[4]}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    create_test_store()
