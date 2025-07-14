#!/usr/bin/env python3
"""
Create test data for InventorySync development
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from datetime import datetime, timedelta
import random
from database import SessionLocal, engine
from models import Base, Store, Product, ProductVariant, CustomFieldDefinition, Location
import json

def create_test_data():
    """Create test data for development"""
    db = SessionLocal()
    
    try:
        # Create a test store
        print("🏪 Creating test store...")
        store = Store(
            shopify_domain="test-store.myshopify.com",
            shop_name="Test Development Store",
            email="test@example.com",
            currency="USD",
            timezone="America/New_York",
            subscription_plan="pro",
            subscription_status="active",
            trial_ends_at=datetime.utcnow() + timedelta(days=14),
            access_token="test-token-development-only",
            is_active=True
        )
        db.add(store)
        db.commit()
        
        # Create locations
        print("📍 Creating locations...")
        main_location = Location(
            store_id=store.id,
            shopify_location_id="1234567890",
            name="Main Warehouse",
            address="123 Warehouse St",
            city="New York",
            country="US",
            is_active=True,
            manages_inventory=True
        )
        db.add(main_location)
        
        retail_location = Location(
            store_id=store.id,
            shopify_location_id="0987654321",
            name="Retail Store",
            address="456 Shop Ave",
            city="Los Angeles",
            country="US",
            is_active=True,
            manages_inventory=True
        )
        db.add(retail_location)
        db.commit()
        
        # Create custom field definitions
        print("🔧 Creating custom field definitions...")
        
        # Product custom fields
        custom_fields = [
            CustomFieldDefinition(
                store_id=store.id,
                field_name="supplier_code",
                display_name="Supplier Code",
                field_type="text",
                target_entity="product",
                is_required=False,
                is_searchable=True,
                is_filterable=True,
                display_order=1,
                help_text="Enter the supplier's product code",
                field_group="Supplier Information"
            ),
            CustomFieldDefinition(
                store_id=store.id,
                field_name="warehouse_location",
                display_name="Warehouse Location",
                field_type="text",
                target_entity="product",
                is_required=False,
                is_searchable=True,
                is_filterable=True,
                display_order=2,
                help_text="Aisle and shelf location in warehouse",
                field_group="Warehouse"
            ),
            CustomFieldDefinition(
                store_id=store.id,
                field_name="reorder_lead_time",
                display_name="Reorder Lead Time (days)",
                field_type="number",
                target_entity="product",
                is_required=False,
                is_searchable=False,
                is_filterable=True,
                display_order=3,
                help_text="Number of days to receive new stock",
                default_value="7",
                field_group="Inventory Management"
            ),
            CustomFieldDefinition(
                store_id=store.id,
                field_name="country_of_origin",
                display_name="Country of Origin",
                field_type="select",
                target_entity="product",
                validation_rules={"options": ["USA", "China", "India", "Germany", "Japan", "Other"]},
                is_required=False,
                is_searchable=False,
                is_filterable=True,
                display_order=4,
                help_text="Select the country where the product is manufactured",
                field_group="Product Details"
            ),
            CustomFieldDefinition(
                store_id=store.id,
                field_name="fragile",
                display_name="Fragile Item",
                field_type="boolean",
                target_entity="product",
                is_required=False,
                is_searchable=False,
                is_filterable=True,
                display_order=5,
                help_text="Check if item requires special handling",
                default_value="false",
                field_group="Shipping"
            ),
            CustomFieldDefinition(
                store_id=store.id,
                field_name="expiry_date",
                display_name="Expiry Date",
                field_type="date",
                target_entity="variant",
                is_required=False,
                is_searchable=False,
                is_filterable=True,
                display_order=6,
                help_text="Product expiration date",
                field_group="Product Details"
            )
        ]
        
        for field in custom_fields:
            db.add(field)
        db.commit()
        
        # Create sample products
        print("📦 Creating sample products...")
        
        sample_products = [
            {
                "title": "Wireless Bluetooth Headphones",
                "handle": "wireless-bluetooth-headphones",
                "product_type": "Electronics",
                "vendor": "TechCorp",
                "tags": "audio,wireless,bluetooth",
                "body_html": "<p>Premium wireless headphones with noise cancellation</p>",
                "variants": [
                    {"title": "Black", "sku": "WBH-001-BLK", "price": 79.99, "inventory": 50},
                    {"title": "White", "sku": "WBH-001-WHT", "price": 79.99, "inventory": 30},
                    {"title": "Blue", "sku": "WBH-001-BLU", "price": 79.99, "inventory": 25}
                ],
                "custom_data": {
                    "supplier_code": "TECH-WBH-001",
                    "warehouse_location": "A1-B2",
                    "reorder_lead_time": 14,
                    "country_of_origin": "China",
                    "fragile": False
                }
            },
            {
                "title": "Organic Green Tea Set",
                "handle": "organic-green-tea-set",
                "product_type": "Food & Beverage",
                "vendor": "TeaHouse",
                "tags": "tea,organic,beverage",
                "body_html": "<p>Premium organic green tea collection</p>",
                "variants": [
                    {"title": "50g Pack", "sku": "TEA-GRN-050", "price": 15.99, "inventory": 100},
                    {"title": "100g Pack", "sku": "TEA-GRN-100", "price": 28.99, "inventory": 60},
                    {"title": "Gift Set", "sku": "TEA-GRN-GIFT", "price": 49.99, "inventory": 20}
                ],
                "custom_data": {
                    "supplier_code": "TEA-ORG-GRN",
                    "warehouse_location": "C3-D1",
                    "reorder_lead_time": 21,
                    "country_of_origin": "Japan",
                    "fragile": True
                }
            },
            {
                "title": "Yoga Mat Premium",
                "handle": "yoga-mat-premium",
                "product_type": "Sports & Fitness",
                "vendor": "FitGear",
                "tags": "yoga,fitness,mat",
                "body_html": "<p>Extra thick premium yoga mat with carrying strap</p>",
                "variants": [
                    {"title": "Purple 6mm", "sku": "YOGA-MAT-PUR-6", "price": 35.99, "inventory": 40},
                    {"title": "Gray 6mm", "sku": "YOGA-MAT-GRY-6", "price": 35.99, "inventory": 35},
                    {"title": "Purple 8mm", "sku": "YOGA-MAT-PUR-8", "price": 42.99, "inventory": 25},
                    {"title": "Gray 8mm", "sku": "YOGA-MAT-GRY-8", "price": 42.99, "inventory": 20}
                ],
                "custom_data": {
                    "supplier_code": "FIT-YOGA-001",
                    "warehouse_location": "B2-C3",
                    "reorder_lead_time": 10,
                    "country_of_origin": "India",
                    "fragile": False
                }
            },
            {
                "title": "Stainless Steel Water Bottle",
                "handle": "stainless-steel-water-bottle",
                "product_type": "Home & Kitchen",
                "vendor": "EcoLife",
                "tags": "bottle,eco-friendly,kitchen",
                "body_html": "<p>Insulated stainless steel water bottle - 24 hours cold, 12 hours hot</p>",
                "variants": [
                    {"title": "500ml Silver", "sku": "BTL-SS-500-SLV", "price": 24.99, "inventory": 75},
                    {"title": "500ml Black", "sku": "BTL-SS-500-BLK", "price": 24.99, "inventory": 80},
                    {"title": "750ml Silver", "sku": "BTL-SS-750-SLV", "price": 29.99, "inventory": 50},
                    {"title": "750ml Black", "sku": "BTL-SS-750-BLK", "price": 29.99, "inventory": 45}
                ],
                "custom_data": {
                    "supplier_code": "ECO-BTL-SS",
                    "warehouse_location": "D4-E2",
                    "reorder_lead_time": 7,
                    "country_of_origin": "Germany",
                    "fragile": False
                }
            },
            {
                "title": "Ceramic Coffee Mug Set",
                "handle": "ceramic-coffee-mug-set",
                "product_type": "Home & Kitchen",
                "vendor": "CeramicArt",
                "tags": "mug,coffee,ceramic,kitchen",
                "body_html": "<p>Handcrafted ceramic coffee mug set - Set of 4</p>",
                "variants": [
                    {"title": "Classic White", "sku": "MUG-CER-WHT-4", "price": 39.99, "inventory": 30},
                    {"title": "Ocean Blue", "sku": "MUG-CER-BLU-4", "price": 44.99, "inventory": 20},
                    {"title": "Earth Tones", "sku": "MUG-CER-ERT-4", "price": 44.99, "inventory": 15}
                ],
                "custom_data": {
                    "supplier_code": "CER-MUG-SET4",
                    "warehouse_location": "E3-F1",
                    "reorder_lead_time": 28,
                    "country_of_origin": "USA",
                    "fragile": True
                }
            }
        ]
        
        for product_data in sample_products:
            # Create product
            product = Product(
                store_id=store.id,
                shopify_product_id=str(random.randint(1000000000, 9999999999)),
                title=product_data["title"],
                handle=product_data["handle"],
                product_type=product_data["product_type"],
                vendor=product_data["vendor"],
                tags=product_data["tags"],
                body_html=product_data["body_html"],
                status="active",
                custom_data=product_data.get("custom_data", {})
            )
            db.add(product)
            db.flush()
            
            # Create variants
            for variant_data in product_data["variants"]:
                variant = ProductVariant(
                    product_id=product.id,
                    shopify_variant_id=str(random.randint(1000000000, 9999999999)),
                    title=variant_data["title"],
                    sku=variant_data["sku"],
                    price=variant_data["price"],
                    inventory_quantity=variant_data["inventory"],
                    inventory_management="shopify",
                    inventory_policy="deny",
                    weight=random.uniform(0.1, 2.0),
                    weight_unit="kg"
                )
                
                # Add expiry date for food items
                if product.product_type == "Food & Beverage":
                    variant.custom_data = {
                        "expiry_date": (datetime.utcnow() + timedelta(days=180)).isoformat()
                    }
                
                db.add(variant)
        
        db.commit()
        
        print("\n✅ Test data created successfully!")
        print(f"   - Store: {store.shop_name}")
        print(f"   - Locations: {db.query(Location).filter_by(store_id=store.id).count()}")
        print(f"   - Products: {db.query(Product).filter_by(store_id=store.id).count()}")
        print(f"   - Variants: {db.query(ProductVariant).join(Product).filter(Product.store_id == store.id).count()}")
        print(f"   - Custom Fields: {db.query(CustomFieldDefinition).filter_by(store_id=store.id).count()}")
        
        print("\n📱 To connect to a real Shopify store:")
        print("   1. Create an app in your Shopify Partners dashboard")
        print("   2. Update the SHOPIFY_API_KEY and SHOPIFY_API_SECRET in backend/.env")
        print("   3. Install the app on a development store")
        print("   4. The OAuth flow will handle the connection automatically")
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()
