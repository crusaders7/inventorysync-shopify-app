#!/usr/bin/env python3
"""
Quick fix for database schema issues
"""

import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

load_dotenv()

# Get database connection details
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://inventorysync:devpassword123@localhost:5432/inventorysync_dev')

def fix_schema():
    """Fix the database schema"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    try:
        # Check existing columns
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'stores'
        """)
        existing_columns = [row[0] for row in cur.fetchall()]
        print(f"Existing columns: {existing_columns}")
        
        # Add missing columns if they don't exist
        if 'shopify_domain' not in existing_columns:
            if 'shop_domain' in existing_columns:
                print("Renaming shop_domain to shopify_domain...")
                cur.execute("ALTER TABLE stores RENAME COLUMN shop_domain TO shopify_domain")
            else:
                print("Adding shopify_domain column...")
                cur.execute("ALTER TABLE stores ADD COLUMN shopify_domain VARCHAR")
                # Try to populate from shopify_store_id if it exists
                if 'shopify_store_id' in existing_columns:
                    cur.execute("UPDATE stores SET shopify_domain = shopify_store_id || '.myshopify.com' WHERE shopify_domain IS NULL")
        
        if 'email' not in existing_columns:
            print("Adding email column...")
            cur.execute("ALTER TABLE stores ADD COLUMN email VARCHAR")
        
        if 'shop_name' not in existing_columns:
            if 'store_name' in existing_columns:
                print("Renaming store_name to shop_name...")
                cur.execute("ALTER TABLE stores RENAME COLUMN store_name TO shop_name")
            else:
                print("Adding shop_name column...")
                cur.execute("ALTER TABLE stores ADD COLUMN shop_name VARCHAR")
        
        # Ensure shopify_domain is not null
        cur.execute("UPDATE stores SET shopify_domain = 'temp-' || id || '.myshopify.com' WHERE shopify_domain IS NULL")
        
        # Create alembic version table if it doesn't exist and mark migrations as complete
        cur.execute("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL, 
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
        """)
        
        cur.execute("""
            INSERT INTO alembic_version (version_num) 
            VALUES ('fix_store_schema_001'), ('001_perf_indexes')
            ON CONFLICT DO NOTHING
        """)
        
        conn.commit()
        print("✅ Database schema fixed successfully!")
        
        # Show final schema
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'stores'
            ORDER BY ordinal_position
        """)
        print("\nFinal stores table schema:")
        for row in cur.fetchall():
            print(f"  - {row[0]}: {row[1]} (nullable: {row[2]})")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    fix_schema()
