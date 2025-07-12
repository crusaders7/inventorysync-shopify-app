#!/usr/bin/env python3
"""Inspect database structure"""

import sqlite3

conn = sqlite3.connect('inventorysync_dev.db')
cursor = conn.cursor()

print("=== STORES TABLE ===")
cursor.execute("PRAGMA table_info(stores)")
columns = cursor.fetchall()
print("Columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

print("\n=== STORES DATA ===")
cursor.execute("SELECT * FROM stores LIMIT 5")
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(f"Row: {row}")
else:
    print("No data in stores table")

print("\n=== CUSTOM_FIELD_DEFINITIONS TABLE ===")
cursor.execute("PRAGMA table_info(custom_field_definitions)")
columns = cursor.fetchall()
if columns:
    print("Columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
else:
    print("Table does not exist")

conn.close()
