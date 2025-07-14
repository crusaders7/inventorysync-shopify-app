#!/usr/bin/env python3
"""
Initialize database tables for InventorySync
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from database import engine, Base
from models import (
    Store, Location, Product, ProductVariant,
    InventoryItem, InventoryMovement, Alert, AlertTemplate,
    Forecast, Supplier, PurchaseOrder, PurchaseOrderLineItem,
    CustomFieldDefinition, WorkflowRule, WorkflowExecution
)

def init_database():
    """Initialize all database tables"""
    print("Initializing InventorySync database...")
    print(f"Database URL: {os.getenv('DATABASE_URL', 'Not set')}")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        # List created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n📊 Created {len(tables)} tables:")
        for table in sorted(tables):
            print(f"  • {table}")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_database()
