#!/usr/bin/env python3
"""
Database Migration Script - Fix Schema Issues
Adds missing columns and creates proper tables
"""

import sqlite3
import sys
import os
from datetime import datetime

def migrate_database():
    """Run database migrations to fix schema issues"""
    
    # Ensure we're in the right directory
    db_path = 'inventorysync_dev.db'
    if not os.path.exists(db_path):
        # Try backend directory
        if os.path.exists('../inventorysync_dev.db'):
            db_path = '../inventorysync_dev.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Starting database migration...")
        
        # 1. Check if stores table exists, if not create it
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shopify_store_id TEXT UNIQUE NOT NULL,
                shop_domain TEXT NOT NULL,
                store_name TEXT NOT NULL,
                currency TEXT DEFAULT 'USD',
                timezone TEXT DEFAULT 'UTC',
                subscription_plan TEXT DEFAULT 'starter',
                subscription_status TEXT DEFAULT 'trial',
                trial_ends_at TIMESTAMP,
                shopify_charge_id TEXT,
                billing_cycle_start TIMESTAMP,
                billing_cycle_end TIMESTAMP,
                plan_price REAL DEFAULT 0.0,
                usage_charges REAL DEFAULT 0.0,
                billing_currency TEXT DEFAULT 'USD',
                deletion_scheduled_at TIMESTAMP,
                access_token TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ Stores table verified/created")
        
        # 2. Check if shopify_store_id column exists, if not add it
        cursor.execute("PRAGMA table_info(stores)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'shopify_store_id' not in columns:
            print("Adding shopify_store_id column...")
            # Since SQLite doesn't support ALTER TABLE ADD COLUMN easily with constraints,
            # we need to recreate the table
            cursor.execute("""
                CREATE TABLE stores_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shopify_store_id TEXT UNIQUE NOT NULL,
                    shop_domain TEXT NOT NULL,
                    store_name TEXT NOT NULL,
                    currency TEXT DEFAULT 'USD',
                    timezone TEXT DEFAULT 'UTC',
                    subscription_plan TEXT DEFAULT 'starter',
                    subscription_status TEXT DEFAULT 'trial',
                    trial_ends_at TIMESTAMP,
                    shopify_charge_id TEXT,
                    billing_cycle_start TIMESTAMP,
                    billing_cycle_end TIMESTAMP,
                    plan_price REAL DEFAULT 0.0,
                    usage_charges REAL DEFAULT 0.0,
                    billing_currency TEXT DEFAULT 'USD',
                    deletion_scheduled_at TIMESTAMP,
                    access_token TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Copy any existing data
            cursor.execute("SELECT COUNT(*) FROM stores")
            count = cursor.fetchone()[0]
            if count > 0:
                cursor.execute("""
                    INSERT INTO stores_new (id, shop_domain, store_name, access_token, created_at, updated_at)
                    SELECT id, 
                           COALESCE(shopify_domain, shop_domain, 'unknown'), 
                           COALESCE(store_name, 'Unknown Store'),
                           COALESCE(access_token, 'dummy_token'),
                           created_at,
                           updated_at
                    FROM stores
                """)
                
                # Generate shopify_store_id for existing records
                cursor.execute("UPDATE stores_new SET shopify_store_id = 'store_' || id WHERE shopify_store_id IS NULL")
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE stores")
            cursor.execute("ALTER TABLE stores_new RENAME TO stores")
            print("✓ Added shopify_store_id column")
        
        # 3. Insert a test store if no stores exist
        cursor.execute("SELECT COUNT(*) FROM stores")
        if cursor.fetchone()[0] == 0:
            print("Inserting test store...")
            cursor.execute("""
                INSERT INTO stores (
                    shopify_store_id, shop_domain, store_name, access_token
                ) VALUES (
                    'test_store_123', 
                    'inventorysync-dev.myshopify.com', 
                    'InventorySync Dev Store',
                    'test_access_token'
                )
            """)
            print("✓ Test store inserted")
        
        # 4. Create custom_field_definitions table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_field_definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id INTEGER NOT NULL,
                field_name TEXT NOT NULL,
                field_type TEXT NOT NULL,
                display_name TEXT NOT NULL,
                description TEXT DEFAULT '',
                required BOOLEAN DEFAULT 0,
                default_value TEXT,
                validation_rules TEXT DEFAULT '{}',
                category TEXT DEFAULT 'product',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (store_id) REFERENCES stores(id),
                UNIQUE(store_id, field_name, category)
            )
        """)
        print("✓ Custom field definitions table verified/created")
        
        # 5. Create alerts table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id INTEGER NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT DEFAULT 'medium',
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                product_sku TEXT,
                location_name TEXT,
                current_stock INTEGER,
                recommended_action TEXT,
                alert_source TEXT DEFAULT 'system',
                entity_type TEXT,
                entity_id INTEGER,
                custom_data TEXT DEFAULT '{}',
                notification_channels TEXT DEFAULT '[]',
                is_acknowledged BOOLEAN DEFAULT 0,
                acknowledged_at TIMESTAMP,
                acknowledged_by TEXT,
                is_resolved BOOLEAN DEFAULT 0,
                resolved_at TIMESTAMP,
                resolved_by TEXT,
                resolution_notes TEXT,
                auto_resolve_at TIMESTAMP,
                is_auto_resolvable BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (store_id) REFERENCES stores(id)
            )
        """)
        print("✓ Alerts table verified/created")
        
        # 6. Create alert_templates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id INTEGER NOT NULL,
                template_name TEXT NOT NULL,
                description TEXT,
                alert_type TEXT NOT NULL,
                title_template TEXT NOT NULL,
                message_template TEXT NOT NULL,
                severity TEXT DEFAULT 'medium',
                trigger_conditions TEXT DEFAULT '{}',
                notification_channels TEXT DEFAULT '[]',
                notification_config TEXT DEFAULT '{}',
                is_active BOOLEAN DEFAULT 1,
                auto_resolve_hours INTEGER,
                usage_count INTEGER DEFAULT 0,
                last_used_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (store_id) REFERENCES stores(id)
            )
        """)
        print("✓ Alert templates table verified/created")
        
        # 7. Create workflow_rules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id INTEGER NOT NULL,
                rule_name TEXT NOT NULL,
                description TEXT,
                trigger_event TEXT NOT NULL,
                trigger_conditions TEXT DEFAULT '{}',
                actions TEXT DEFAULT '[]',
                is_active BOOLEAN DEFAULT 1,
                execution_count INTEGER DEFAULT 0,
                last_executed_at TIMESTAMP,
                priority INTEGER DEFAULT 100,
                max_executions_per_hour INTEGER DEFAULT 60,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (store_id) REFERENCES stores(id)
            )
        """)
        print("✓ Workflow rules table verified/created")
        
        # 8. Fix shopify_domain column name issue in custom_fields.py
        # The code looks for 'shopify_domain' but the column is 'shop_domain'
        cursor.execute("PRAGMA table_info(stores)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'shopify_domain' not in columns and 'shop_domain' in columns:
            # No need to rename, we'll fix the code instead
            print("✓ Note: shop_domain column exists (code will be updated)")
        
        # Commit all changes
        conn.commit()
        print("\n✅ Database migration completed successfully!")
        
        # Show current stores
        cursor.execute("SELECT id, shopify_store_id, shop_domain, store_name FROM stores")
        stores = cursor.fetchall()
        if stores:
            print("\nCurrent stores in database:")
            for store in stores:
                print(f"  ID: {store[0]}, Store ID: {store[1]}, Domain: {store[2]}, Name: {store[3]}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
