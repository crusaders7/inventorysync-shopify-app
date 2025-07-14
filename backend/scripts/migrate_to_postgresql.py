#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script
Exports data from SQLite and imports into PostgreSQL
"""

import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration
SQLITE_DB = "inventorysync_dev.db"
POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql://inventorysync:devpassword123@localhost:5432/inventorysync_dev")

# Parse PostgreSQL URL
import urllib.parse
url = urllib.parse.urlparse(POSTGRES_URL)


def migrate_data():
    """Migrate all data from SQLite to PostgreSQL"""
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(
        host=url.hostname,
        port=url.port,
        database=url.path[1:],
        user=url.username,
        password=url.password
    )
    pg_cursor = pg_conn.cursor()
    
    try:
        print("Starting migration from SQLite to PostgreSQL...")
        
        # Tables to migrate in order (respecting foreign keys)
        tables = [
            "stores",
            "locations", 
            "products",
            "product_variants",
            "inventory_items",
            "inventory_movements",
            "suppliers",
            "purchase_orders",
            "purchase_order_line_items",
            "alerts",
            "alert_templates",
            "custom_field_definitions",
            "workflow_rules",
            "workflow_executions",
            "forecasts"
        ]
        
        for table in tables:
            print(f"\nMigrating table: {table}")
            
            # Get data from SQLite
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                print(f"  No data in {table}")
                continue
            
            # Get column names
            columns = [description[0] for description in sqlite_cursor.description]
            
            # Prepare PostgreSQL insert
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join([f'"{col}"' for col in columns])
            insert_query = f'INSERT INTO {table} ({columns_str}) VALUES ({placeholders})'
            
            # Insert data
            count = 0
            for row in rows:
                values = []
                for i, col in enumerate(columns):
                    value = row[i]
                    
                    # Handle JSON fields
                    if col in ['custom_data', 'validation_rules', 'trigger_conditions', 
                              'actions', 'notification_channels', 'metadata']:
                        if value and isinstance(value, str):
                            try:
                                # Validate JSON
                                json.loads(value)
                                values.append(value)
                            except:
                                values.append('{}' if 'channels' not in col else '[]')
                        else:
                            values.append('{}' if 'channels' not in col else '[]')
                    else:
                        values.append(value)
                
                try:
                    pg_cursor.execute(insert_query, values)
                    count += 1
                except Exception as e:
                    print(f"  Error inserting row: {e}")
                    print(f"  Values: {values}")
                    continue
            
            pg_conn.commit()
            print(f"  Migrated {count} rows")
        
        # Update sequences for auto-increment fields
        print("\nUpdating sequences...")
        sequence_updates = [
            ("stores_id_seq", "stores"),
            ("products_id_seq", "products"),
            ("alerts_id_seq", "alerts"),
            ("custom_field_definitions_id_seq", "custom_field_definitions"),
            ("workflow_rules_id_seq", "workflow_rules")
        ]
        
        for seq_name, table_name in sequence_updates:
            pg_cursor.execute(f"""
                SELECT setval('{seq_name}', 
                    COALESCE((SELECT MAX(id) FROM {table_name}), 1)
                )
            """)
        
        pg_conn.commit()
        print("\nMigration completed successfully!")
        
        # Verify migration
        print("\nVerifying migration...")
        for table in tables:
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            sqlite_count = sqlite_cursor.fetchone()[0]
            
            pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            pg_count = pg_cursor.fetchone()[0]
            
            status = "✓" if sqlite_count == pg_count else "✗"
            print(f"  {status} {table}: SQLite={sqlite_count}, PostgreSQL={pg_count}")
    
    except Exception as e:
        print(f"\nError during migration: {e}")
        pg_conn.rollback()
        raise
    finally:
        sqlite_conn.close()
        pg_conn.close()


def create_indexes():
    """Create performance indexes in PostgreSQL"""
    
    pg_conn = psycopg2.connect(
        host=url.hostname,
        port=url.port,
        database=url.path[1:],
        user=url.username,
        password=url.password
    )
    pg_cursor = pg_conn.cursor()
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_stores_shop_domain ON stores(shop_domain)",
        "CREATE INDEX IF NOT EXISTS idx_products_store_id ON products(store_id)",
        "CREATE INDEX IF NOT EXISTS idx_product_variants_product_id ON product_variants(product_id)",
        "CREATE INDEX IF NOT EXISTS idx_inventory_items_variant_id ON inventory_items(variant_id)",
        "CREATE INDEX IF NOT EXISTS idx_inventory_items_location_id ON inventory_items(location_id)",
        "CREATE INDEX IF NOT EXISTS idx_alerts_store_id_created_at ON alerts(store_id, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_custom_fields_store_id ON custom_field_definitions(store_id)",
        "CREATE INDEX IF NOT EXISTS idx_workflow_rules_store_id ON workflow_rules(store_id)",
        
        # JSONB indexes
        "CREATE INDEX IF NOT EXISTS idx_products_custom_data ON products USING GIN (custom_data)",
        "CREATE INDEX IF NOT EXISTS idx_inventory_custom_data ON inventory_items USING GIN (custom_data)",
        "CREATE INDEX IF NOT EXISTS idx_alerts_custom_data ON alerts USING GIN (custom_data)"
    ]
    
    print("\nCreating indexes...")
    for index in indexes:
        try:
            pg_cursor.execute(index)
            print(f"  ✓ {index.split('idx_')[1].split(' ')[0]}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    pg_conn.commit()
    pg_conn.close()
    print("Index creation completed!")


if __name__ == "__main__":
    # First, make sure PostgreSQL tables are created
    print("Make sure you've updated DATABASE_URL in .env to PostgreSQL")
    print("and run the app once to create tables.\n")
    
    response = input("Have you done this? (yes/no): ")
    if response.lower() != 'yes':
        print("Please update .env and run the app first.")
        exit(1)
    
    migrate_data()
    create_indexes()
    
    print("\n✅ Migration complete!")
    print("\nNext steps:")
    print("1. Update DATABASE_URL in .env to use PostgreSQL")
    print("2. Restart the application")
    print("3. Test all features")
    print("4. Set up regular backups")
