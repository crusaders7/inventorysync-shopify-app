import sqlite3
import os

db_path = os.path.join('backend', 'inventorysync_dev.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tables:", tables)
    
    # Check stores table structure
    cursor.execute("PRAGMA table_info(stores)")
    columns = cursor.fetchall()
    print("\nStores table columns:")
    for col in columns:
        print(f"  {col[1]} - {col[2]}")
    
    conn.close()
else:
    print("Database doesn't exist yet")
