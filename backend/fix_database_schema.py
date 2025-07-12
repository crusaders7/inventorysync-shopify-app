#!/usr/bin/env python3
"""
Fix database schema to match actual database structure
"""

import sqlite3
import os
import sys
from datetime import datetime

def fix_database_schema():
    """Update database schema to match actual table structure"""
    
    # Connect to database
    db_path = "inventorysync_dev.db"
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check current stores table structure
        cursor.execute("PRAGMA table_info(stores);")
        current_columns = {row[1]: row[2] for row in cursor.fetchall()}
        print("Current stores table columns:")
        for col_name, col_type in current_columns.items():
            print(f"  {col_name}: {col_type}")
        
        # Define columns that should exist
        required_columns = {
            'id': 'INTEGER',
            'shopify_domain': 'VARCHAR',
            'access_token': 'VARCHAR', 
            'shop_name': 'VARCHAR',
            'email': 'VARCHAR',
            'created_at': 'DATETIME',
            'updated_at': 'DATETIME'
        }
        
        # Check if we need to add any missing columns
        missing_columns = []
        for col_name, col_type in required_columns.items():
            if col_name not in current_columns:
                missing_columns.append((col_name, col_type))
        
        if missing_columns:
            print(f"\nAdding missing columns: {missing_columns}")
            for col_name, col_type in missing_columns:
                cursor.execute(f"ALTER TABLE stores ADD COLUMN {col_name} {col_type}")
                print(f"Added column: {col_name} {col_type}")
        else:
            print("\nNo missing columns - database schema is correct")
        
        # Commit changes
        conn.commit()
        print("Database schema updated successfully")
        
        # Verify current store data
        cursor.execute("SELECT * FROM stores")
        stores = cursor.fetchall()
        print(f"\nCurrent stores in database: {len(stores)}")
        for store in stores:
            print(f"  Store ID: {store[0]}, Domain: {store[1]}")
        
        return True
        
    except Exception as e:
        print(f"Error fixing database schema: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("Fixing database schema...")
    success = fix_database_schema()
    
    if success:
        print("✅ Database schema fixed successfully")
        sys.exit(0)
    else:
        print("❌ Failed to fix database schema")
        sys.exit(1)