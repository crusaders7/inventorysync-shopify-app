#!/usr/bin/env python3
"""
Setup test data for development/testing
"""
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Store, CustomFieldDefinition
from database import Base

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://inventorysync:devpassword123@localhost/inventorysync_dev")

# Create engine and session
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def setup_test_store():
    """Create a test store if it doesn't exist"""
    try:
        # Check if store exists
        shop_domain = "inventorysync-dev.myshopify.com"
        store = session.query(Store).filter(Store.shopify_domain == shop_domain).first()
        
        if not store:
            # Create test store
            store = Store(
                shopify_domain=shop_domain,
                shopify_store_id="test-store-123",
                store_name="InventorySync Dev Store",
                email="dev@inventorysync.app",
                access_token="dev-token",
                plan_name="development",
                installed_at=datetime.utcnow(),
                is_active=True
            )
            session.add(store)
            session.commit()
            print(f"✓ Created test store: {shop_domain}")
        else:
            print(f"✓ Test store already exists: {shop_domain}")
            
        return store
    except Exception as e:
        session.rollback()
        print(f"✗ Error creating test store: {e}")
        raise

def setup_sample_fields(store):
    """Create some sample custom fields"""
    try:
        # Check if fields already exist
        existing_fields = session.query(CustomFieldDefinition).filter(
            CustomFieldDefinition.store_id == store.id
        ).count()
        
        if existing_fields == 0:
            # Create sample fields
            sample_fields = [
                {
                    "name": "material",
                    "field_type": "text",
                    "label": "Material",
                    "description": "Primary material composition",
                    "is_active": True
                },
                {
                    "name": "weight",
                    "field_type": "number",
                    "label": "Weight (kg)",
                    "description": "Product weight in kilograms",
                    "is_active": True
                },
                {
                    "name": "size",
                    "field_type": "select",
                    "label": "Size",
                    "options": ["Small", "Medium", "Large", "X-Large"],
                    "is_active": True
                }
            ]
            
            for field_data in sample_fields:
                field = CustomFieldDefinition(
                    store_id=store.id,
                    **field_data
                )
                session.add(field)
            
            session.commit()
            print(f"✓ Created {len(sample_fields)} sample custom fields")
        else:
            print(f"✓ Custom fields already exist: {existing_fields} fields")
            
    except Exception as e:
        session.rollback()
        print(f"✗ Error creating sample fields: {e}")
        raise

def main():
    """Main setup function"""
    print("Setting up test data...")
    
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables ready")
        
        # Setup test store
        store = setup_test_store()
        
        # Setup sample fields
        setup_sample_fields(store)
        
        print("\n✅ Test data setup complete!")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    main()
