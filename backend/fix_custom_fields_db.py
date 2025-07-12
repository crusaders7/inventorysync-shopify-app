#!/usr/bin/env python3
"""
Fix Custom Fields Database Issues
"""

import sqlite3
import os

def fix_database():
    """Fix the database for custom fields to work"""
    
    db_path = 'inventorysync_dev.db'
    
    print(f"Working with database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Drop existing stores table if it exists (it has wrong schema)
        cursor.execute("DROP TABLE IF EXISTS stores")
        print("✓ Dropped existing stores table")
        
        # 2. Create stores table with correct schema
        cursor.execute("""
            CREATE TABLE stores (
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
        print("✓ Created stores table with correct schema")
        
        # 3. Insert test store
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
        print("✓ Inserted test store")
        
        # 4. Create custom_field_definitions table
        cursor.execute("DROP TABLE IF EXISTS custom_field_definitions")
        cursor.execute("""
            CREATE TABLE custom_field_definitions (
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
        print("✓ Created custom_field_definitions table")
        
        # 5. Insert some sample custom fields
        cursor.execute("""
            INSERT INTO custom_field_definitions (
                store_id, field_name, field_type, display_name, description, category
            ) VALUES 
            (1, 'material', 'text', 'Material', 'Product material type', 'product'),
            (1, 'size', 'select', 'Size', 'Product size', 'product'),
            (1, 'color', 'text', 'Color', 'Product color', 'product')
        """)
        print("✓ Inserted sample custom fields")
        
        # 6. Create other necessary tables
        cursor.execute("DROP TABLE IF EXISTS alerts")
        cursor.execute("""
            CREATE TABLE alerts (
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
        print("✓ Created alerts table")
        
        cursor.execute("DROP TABLE IF EXISTS alert_templates")
        cursor.execute("""
            CREATE TABLE alert_templates (
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
        print("✓ Created alert_templates table")
        
        cursor.execute("DROP TABLE IF EXISTS workflow_rules")
        cursor.execute("""
            CREATE TABLE workflow_rules (
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
        print("✓ Created workflow_rules table")
        
        # Insert sample alerts
        cursor.execute("""
            INSERT INTO alerts (store_id, alert_type, severity, title, message)
            VALUES
            (1, 'low_stock', 'high', 'Low Stock Alert', 'Product ABC is running low on stock'),
            (1, 'overstock', 'medium', 'Overstock Warning', 'Product XYZ has excess inventory')
        """)
        print("✓ Inserted sample alerts")
        
        # Commit all changes
        conn.commit()
        print("\n✅ Database fixed successfully!")
        
        # Verify the fix
        print("\nVerifying database structure:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("Tables:", [t[0] for t in tables])
        
        cursor.execute("SELECT COUNT(*) FROM stores")
        print(f"Stores count: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM custom_field_definitions")
        print(f"Custom fields count: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM alerts")
        print(f"Alerts count: {cursor.fetchone()[0]}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database()
