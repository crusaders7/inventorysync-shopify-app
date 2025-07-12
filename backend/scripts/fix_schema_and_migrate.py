#!/usr/bin/env python3
"""
Fix schema differences and complete PostgreSQL migration
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


def fix_location_data(sqlite_row):
    """Convert SQLite location data to PostgreSQL format"""
    # Combine address fields into single address
    address_parts = []
    if sqlite_row['address1']:
        address_parts.append(sqlite_row['address1'])
    if sqlite_row['address2']:
        address_parts.append(sqlite_row['address2'])
    if sqlite_row['zip']:
        address_parts.append(sqlite_row['zip'])
    if sqlite_row['province']:
        address_parts.append(sqlite_row['province'])
    
    address = ', '.join(address_parts) if address_parts else None
    
    return {
        'id': sqlite_row['id'],
        'store_id': sqlite_row['store_id'],
        'shopify_location_id': sqlite_row['shopify_location_id'],
        'name': sqlite_row['name'],
        'address': address,
        'city': sqlite_row['city'],
        'country': sqlite_row['country'],
        'is_active': bool(sqlite_row['active']),
        'manages_inventory': True,  # Default to True
        'created_at': sqlite_row['created_at'],
        'updated_at': sqlite_row['updated_at']
    }


def fix_product_data(sqlite_row):
    """Convert SQLite product data to PostgreSQL format"""
    # Remove fields that don't exist in PostgreSQL
    return {
        'id': sqlite_row['id'],
        'store_id': sqlite_row['store_id'],
        'shopify_product_id': sqlite_row['shopify_product_id'],
        'title': sqlite_row['title'],
        'handle': sqlite_row['handle'],
        'product_type': sqlite_row['product_type'],
        'vendor': sqlite_row['vendor'],
        'price': None,  # Will be set from variants
        'cost_per_item': None,
        'status': sqlite_row['status'],
        'custom_data': json.dumps({}),
        'created_at': sqlite_row['created_at'],
        'updated_at': sqlite_row['updated_at']
    }


def fix_variant_data(sqlite_row):
    """Convert SQLite variant data to PostgreSQL format"""
    return {
        'id': sqlite_row['id'],
        'product_id': sqlite_row['product_id'],
        'shopify_variant_id': sqlite_row['shopify_variant_id'],
        'title': sqlite_row['title'],
        'sku': sqlite_row['sku'],
        'barcode': sqlite_row['barcode'],
        'price': sqlite_row['price'],
        'cost_per_item': sqlite_row['compare_at_price'],  # Using compare_at_price as cost
        'weight': sqlite_row['weight'],
        'weight_unit': sqlite_row['weight_unit'],
        'requires_shipping': True,  # Default to True
        'track_inventory': sqlite_row['inventory_management'] == 'shopify' if sqlite_row['inventory_management'] else False,
        'inventory_policy': sqlite_row['inventory_policy'],
        'custom_data': json.dumps({}),
        'created_at': sqlite_row['created_at'],
        'updated_at': sqlite_row['updated_at']
    }


def fix_alert_data(sqlite_row):
    """Convert SQLite alert data to PostgreSQL format"""
    return {
        'id': sqlite_row['id'],
        'store_id': sqlite_row['store_id'],
        'alert_type': sqlite_row['alert_type'],
        'severity': sqlite_row['severity'],
        'title': sqlite_row['title'],
        'message': sqlite_row['message'],
        'product_sku': sqlite_row['product_sku'],
        'location_name': sqlite_row['location_name'],
        'current_stock': sqlite_row['current_stock'],
        'recommended_action': sqlite_row['recommended_action'],
        'alert_source': sqlite_row['alert_source'],
        'entity_type': sqlite_row['entity_type'],
        'entity_id': sqlite_row['entity_id'],
        'custom_data': sqlite_row['custom_data'] if sqlite_row['custom_data'] else json.dumps({}),
        'notification_channels': sqlite_row['notification_channels'] if sqlite_row['notification_channels'] else json.dumps([]),
        'is_acknowledged': bool(sqlite_row['is_acknowledged']),
        'acknowledged_at': sqlite_row['acknowledged_at'],
        'acknowledged_by': sqlite_row['acknowledged_by'],
        'is_resolved': bool(sqlite_row['is_resolved']),
        'resolved_at': sqlite_row['resolved_at'],
        'resolved_by': sqlite_row['resolved_by'],
        'resolution_notes': sqlite_row['resolution_notes'],
        'auto_resolve_at': sqlite_row['auto_resolve_at'],
        'is_auto_resolvable': bool(sqlite_row['is_auto_resolvable']),
        'created_at': sqlite_row['created_at'],
        'updated_at': sqlite_row['updated_at']
    }


def fix_custom_field_data(sqlite_row):
    """Convert SQLite custom field data to PostgreSQL format"""
    return {
        'id': sqlite_row['id'],
        'store_id': sqlite_row['store_id'],
        'field_name': sqlite_row['field_name'],
        'display_name': sqlite_row['display_name'],
        'field_type': sqlite_row['field_type'],
        'target_entity': sqlite_row['category'] if sqlite_row['category'] else 'product',  # Map category to target_entity
        'validation_rules': sqlite_row['validation_rules'] if sqlite_row['validation_rules'] else json.dumps({}),
        'is_required': bool(sqlite_row['required']),  # 'required' not 'is_required' in SQLite
        'is_searchable': True,
        'is_filterable': True,
        'display_order': 0,
        'help_text': sqlite_row['description'] if sqlite_row['description'] else None,
        'default_value': sqlite_row['default_value'],
        'field_group': 'basic',
        'industry_template': None,
        'is_active': True,
        'created_at': sqlite_row['created_at'],
        'updated_at': sqlite_row['updated_at']
    }


def migrate_with_fixes():
    """Migrate all data with schema fixes"""
    
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
        print("Starting migration with schema fixes...")
        
        # Clear existing data (except stores which already migrated)
        tables_to_clear = [
            "locations", "products", "product_variants", "inventory_items",
            "inventory_movements", "alerts", "alert_templates", 
            "custom_field_definitions", "workflow_rules", "workflow_executions",
            "forecasts", "suppliers", "purchase_orders", "purchase_order_line_items"
        ]
        
        for table in tables_to_clear:
            pg_cursor.execute(f"TRUNCATE TABLE {table} CASCADE")
        pg_conn.commit()
        print("Cleared existing data")
        
        # Migrate locations with fixes
        print("\nMigrating locations...")
        sqlite_cursor.execute("SELECT * FROM locations")
        locations = sqlite_cursor.fetchall()
        
        for loc in locations:
            fixed_loc = fix_location_data(dict(loc))
            pg_cursor.execute("""
                INSERT INTO locations (id, store_id, shopify_location_id, name, 
                                     address, city, country, is_active, manages_inventory,
                                     created_at, updated_at)
                VALUES (%(id)s, %(store_id)s, %(shopify_location_id)s, %(name)s,
                       %(address)s, %(city)s, %(country)s, %(is_active)s, %(manages_inventory)s,
                       %(created_at)s, %(updated_at)s)
            """, fixed_loc)
        print(f"  Migrated {len(locations)} locations")
        
        # Migrate products with fixes
        print("\nMigrating products...")
        sqlite_cursor.execute("SELECT * FROM products")
        products = sqlite_cursor.fetchall()
        
        for prod in products:
            fixed_prod = fix_product_data(dict(prod))
            pg_cursor.execute("""
                INSERT INTO products (id, store_id, shopify_product_id, title, handle,
                                    product_type, vendor, price, cost_per_item, status,
                                    custom_data, created_at, updated_at)
                VALUES (%(id)s, %(store_id)s, %(shopify_product_id)s, %(title)s, %(handle)s,
                       %(product_type)s, %(vendor)s, %(price)s, %(cost_per_item)s, %(status)s,
                       %(custom_data)s, %(created_at)s, %(updated_at)s)
            """, fixed_prod)
        print(f"  Migrated {len(products)} products")
        
        # Migrate variants with fixes
        print("\nMigrating product variants...")
        sqlite_cursor.execute("SELECT * FROM product_variants")
        variants = sqlite_cursor.fetchall()
        
        for var in variants:
            fixed_var = fix_variant_data(dict(var))
            pg_cursor.execute("""
                INSERT INTO product_variants (id, product_id, shopify_variant_id, title, sku,
                                            barcode, price, cost_per_item, weight, weight_unit,
                                            requires_shipping, track_inventory, inventory_policy,
                                            custom_data, created_at, updated_at)
                VALUES (%(id)s, %(product_id)s, %(shopify_variant_id)s, %(title)s, %(sku)s,
                       %(barcode)s, %(price)s, %(cost_per_item)s, %(weight)s, %(weight_unit)s,
                       %(requires_shipping)s, %(track_inventory)s, %(inventory_policy)s,
                       %(custom_data)s, %(created_at)s, %(updated_at)s)
            """, fixed_var)
        print(f"  Migrated {len(variants)} variants")
        
        # Migrate alerts with fixes
        print("\nMigrating alerts...")
        sqlite_cursor.execute("SELECT * FROM alerts")
        alerts = sqlite_cursor.fetchall()
        
        for alert in alerts:
            fixed_alert = fix_alert_data(dict(alert))
            pg_cursor.execute("""
                INSERT INTO alerts (id, store_id, alert_type, severity, title, message,
                                  product_sku, location_name, current_stock, recommended_action,
                                  alert_source, entity_type, entity_id, custom_data,
                                  notification_channels, is_acknowledged, acknowledged_at,
                                  acknowledged_by, is_resolved, resolved_at, resolved_by,
                                  resolution_notes, auto_resolve_at, is_auto_resolvable,
                                  created_at, updated_at)
                VALUES (%(id)s, %(store_id)s, %(alert_type)s, %(severity)s, %(title)s, %(message)s,
                       %(product_sku)s, %(location_name)s, %(current_stock)s, %(recommended_action)s,
                       %(alert_source)s, %(entity_type)s, %(entity_id)s, %(custom_data)s,
                       %(notification_channels)s, %(is_acknowledged)s, %(acknowledged_at)s,
                       %(acknowledged_by)s, %(is_resolved)s, %(resolved_at)s, %(resolved_by)s,
                       %(resolution_notes)s, %(auto_resolve_at)s, %(is_auto_resolvable)s,
                       %(created_at)s, %(updated_at)s)
            """, fixed_alert)
        print(f"  Migrated {len(alerts)} alerts")
        
        # Migrate custom fields with fixes
        print("\nMigrating custom field definitions...")
        sqlite_cursor.execute("SELECT * FROM custom_field_definitions")
        custom_fields = sqlite_cursor.fetchall()
        
        for cf in custom_fields:
            fixed_cf = fix_custom_field_data(dict(cf))
            pg_cursor.execute("""
                INSERT INTO custom_field_definitions (id, store_id, field_name, display_name,
                                                    field_type, target_entity, validation_rules,
                                                    is_required, is_searchable, is_filterable,
                                                    display_order, help_text, default_value,
                                                    field_group, industry_template, is_active,
                                                    created_at, updated_at)
                VALUES (%(id)s, %(store_id)s, %(field_name)s, %(display_name)s,
                       %(field_type)s, %(target_entity)s, %(validation_rules)s,
                       %(is_required)s, %(is_searchable)s, %(is_filterable)s,
                       %(display_order)s, %(help_text)s, %(default_value)s,
                       %(field_group)s, %(industry_template)s, %(is_active)s,
                       %(created_at)s, %(updated_at)s)
            """, fixed_cf)
        print(f"  Migrated {len(custom_fields)} custom field definitions")
        
        # Update sequences
        print("\nUpdating sequences...")
        sequences = [
            ("locations_id_seq", "locations"),
            ("products_id_seq", "products"),
            ("product_variants_id_seq", "product_variants"),
            ("alerts_id_seq", "alerts"),
            ("custom_field_definitions_id_seq", "custom_field_definitions")
        ]
        
        for seq_name, table_name in sequences:
            pg_cursor.execute(f"""
                SELECT setval('{seq_name}', 
                    COALESCE((SELECT MAX(id) FROM {table_name}), 1)
                )
            """)
        
        pg_conn.commit()
        print("\nMigration completed successfully!")
        
        # Verify migration
        print("\nVerifying migration...")
        verification_tables = ["stores", "locations", "products", "product_variants", "alerts", "custom_field_definitions"]
        
        for table in verification_tables:
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
        # Core indexes
        "CREATE INDEX IF NOT EXISTS idx_stores_shop_domain ON stores(shop_domain)",
        "CREATE INDEX IF NOT EXISTS idx_products_store_id ON products(store_id)",
        "CREATE INDEX IF NOT EXISTS idx_product_variants_product_id ON product_variants(product_id)",
        "CREATE INDEX IF NOT EXISTS idx_product_variants_sku ON product_variants(sku)",
        "CREATE INDEX IF NOT EXISTS idx_inventory_items_variant_id ON inventory_items(variant_id)",
        "CREATE INDEX IF NOT EXISTS idx_inventory_items_location_id ON inventory_items(location_id)",
        "CREATE INDEX IF NOT EXISTS idx_alerts_store_id_created_at ON alerts(store_id, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_custom_fields_store_id ON custom_field_definitions(store_id)",
        "CREATE INDEX IF NOT EXISTS idx_workflow_rules_store_id ON workflow_rules(store_id)",
        
        # Composite indexes for common queries
        "CREATE INDEX IF NOT EXISTS idx_inventory_variant_location ON inventory_items(variant_id, location_id)",
        "CREATE INDEX IF NOT EXISTS idx_alerts_store_type ON alerts(store_id, alert_type)",
        "CREATE INDEX IF NOT EXISTS idx_custom_fields_store_entity ON custom_field_definitions(store_id, target_entity)",
        
        # JSONB indexes - using GIN for PostgreSQL
        "CREATE INDEX IF NOT EXISTS idx_products_custom_data ON products USING GIN ((custom_data::jsonb))",
        "CREATE INDEX IF NOT EXISTS idx_inventory_custom_data ON inventory_items USING GIN ((custom_data::jsonb))",
        "CREATE INDEX IF NOT EXISTS idx_alerts_custom_data ON alerts USING GIN ((custom_data::jsonb))"
    ]
    
    print("\nCreating indexes...")
    for index in indexes:
        try:
            pg_cursor.execute(index)
            index_name = index.split('idx_')[1].split(' ')[0]
            print(f"  ✓ {index_name}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    pg_conn.commit()
    pg_conn.close()
    print("Index creation completed!")


if __name__ == "__main__":
    confirm = input("This will clear and re-migrate all data (except stores). Continue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Migration cancelled.")
        exit(1)
    
    migrate_with_fixes()
    create_indexes()
    
    print("\n✅ Migration complete!")
    print("\nNext steps:")
    print("1. Test all application features")
    print("2. Set up regular backups")
    print("3. Monitor performance")
