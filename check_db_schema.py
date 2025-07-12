#!/usr/bin/env python3
"""Check database schema"""

import sqlite3

def check_schema():
    conn = sqlite3.connect('inventorysync_dev.db')
    cursor = conn.cursor()
    
    # Check stores table
    cursor.execute("PRAGMA table_info(stores)")
    print("Stores table columns:")
    for col in cursor.fetchall():
        print(f"  {col[1]} - {col[2]}")
    
    # Check if shopify_store_id exists
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='stores'")
    result = cursor.fetchone()
    if result:
        print("\nStores table CREATE statement:")
        print(result[0])
    
    conn.close()

if __name__ == "__main__":
    check_schema()
