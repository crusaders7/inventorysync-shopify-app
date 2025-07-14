#!/usr/bin/env python3
"""
Test custom fields creation and validation
"""

import requests
import json
import sqlite3
import sys
from datetime import datetime
from typing import Dict, Any

def test_custom_fields_api():
    """Test custom fields API endpoints"""
    base_url = "http://localhost:8000/api/v1"
    shop_domain = "inventorysync-dev.myshopify.com"
    
    # Test create custom field
    print("🧪 Testing custom field creation...")
    
    custom_field_data = {
        "field_name": "supplier_code",
        "field_type": "text",
        "display_name": "Supplier Code",
        "description": "Internal supplier identification code",
        "required": False,
        "default_value": "",
        "validation_rules": {
            "max_length": 20,
            "pattern": "^[A-Z0-9-]+$"
        },
        "category": "product"
    }
    
    try:
        response = requests.post(f"{base_url}/custom-fields/{shop_domain}", json=custom_field_data)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Custom field created: {result}")
        field_id = result.get("field_id")
        
        # Test list custom fields
        print("\n🧪 Testing custom fields list...")
        response = requests.get(f"{base_url}/custom-fields/{shop_domain}")
        response.raise_for_status()
        
        fields = response.json()
        print(f"✅ Custom fields retrieved: {len(fields.get('fields', []))} fields")
        
        # Test update custom field
        if field_id:
            print(f"\n🧪 Testing custom field update...")
            update_data = {
                "display_name": "Supplier Code (Updated)",
                "description": "Updated supplier identification code",
                "validation_rules": {
                    "max_length": 25,
                    "pattern": "^[A-Z0-9-]+$"
                }
            }
            
            response = requests.put(f"{base_url}/custom-fields/{shop_domain}/{field_id}", json=update_data)
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ Custom field updated: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Custom fields API test failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return False

def test_custom_field_validation():
    """Test custom field validation logic"""
    print("\n🧪 Testing custom field validation...")
    
    # Test validation functions
    validation_tests = [
        {
            "field_type": "text",
            "value": "SUPPLIER-001",
            "validation_rules": {"max_length": 20, "pattern": "^[A-Z0-9-]+$"},
            "expected": True
        },
        {
            "field_type": "text", 
            "value": "supplier-001",
            "validation_rules": {"max_length": 20, "pattern": "^[A-Z0-9-]+$"},
            "expected": False  # lowercase not allowed
        },
        {
            "field_type": "number",
            "value": 15,
            "validation_rules": {"min_value": 0, "max_value": 100},
            "expected": True
        },
        {
            "field_type": "number",
            "value": 150,
            "validation_rules": {"min_value": 0, "max_value": 100},
            "expected": False  # exceeds max
        },
        {
            "field_type": "boolean",
            "value": True,
            "validation_rules": {},
            "expected": True
        },
        {
            "field_type": "date",
            "value": "2025-07-09",
            "validation_rules": {"date_format": "%Y-%m-%d"},
            "expected": True
        }
    ]
    
    # Import validation function
    import re
    from datetime import datetime
    
    def validate_field_value(field_type: str, value: Any, validation_rules: Dict) -> bool:
        """Validate field value based on type and rules"""
        try:
            if field_type == "text":
                if not isinstance(value, str):
                    return False
                
                # Check length
                if "max_length" in validation_rules:
                    if len(value) > validation_rules["max_length"]:
                        return False
                
                # Check pattern
                if "pattern" in validation_rules:
                    if not re.match(validation_rules["pattern"], value):
                        return False
                
                return True
                
            elif field_type == "number":
                if not isinstance(value, (int, float)):
                    return False
                
                # Check min/max
                if "min_value" in validation_rules:
                    if value < validation_rules["min_value"]:
                        return False
                
                if "max_value" in validation_rules:
                    if value > validation_rules["max_value"]:
                        return False
                
                return True
                
            elif field_type == "boolean":
                return isinstance(value, bool)
                
            elif field_type == "date":
                if not isinstance(value, str):
                    return False
                
                # Check date format
                if "date_format" in validation_rules:
                    try:
                        datetime.strptime(value, validation_rules["date_format"])
                        return True
                    except ValueError:
                        return False
                
                return True
                
            return False
            
        except Exception as e:
            print(f"Validation error: {e}")
            return False
    
    # Run validation tests
    passed = 0
    total = len(validation_tests)
    
    for i, test in enumerate(validation_tests):
        result = validate_field_value(
            test["field_type"], 
            test["value"], 
            test["validation_rules"]
        )
        
        if result == test["expected"]:
            print(f"✅ Validation test {i+1}: PASSED")
            passed += 1
        else:
            print(f"❌ Validation test {i+1}: FAILED (expected {test['expected']}, got {result})")
    
    print(f"\n📊 Validation tests: {passed}/{total} passed")
    return passed == total

def test_custom_field_database():
    """Test custom field database operations"""
    print("\n🧪 Testing custom field database operations...")
    
    conn = sqlite3.connect('inventorysync_dev.db')
    cursor = conn.cursor()
    
    try:
        # Create custom_field_definitions table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_field_definitions (
                id INTEGER PRIMARY KEY,
                store_id INTEGER,
                field_name TEXT NOT NULL,
                field_type TEXT NOT NULL,
                display_name TEXT,
                description TEXT,
                required BOOLEAN DEFAULT 0,
                default_value TEXT,
                validation_rules JSON,
                category TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (store_id) REFERENCES stores (id)
            )
        """)
        
        # Get store ID
        cursor.execute("SELECT id FROM stores WHERE shopify_domain = ?", ("inventorysync-dev.myshopify.com",))
        store_result = cursor.fetchone()
        
        if not store_result:
            print("❌ Store not found in database")
            return False
        
        store_id = store_result[0]
        
        # Insert test custom field
        cursor.execute("""
            INSERT INTO custom_field_definitions (
                store_id, field_name, field_type, display_name, description,
                required, default_value, validation_rules, category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            store_id,
            "test_field",
            "text",
            "Test Field",
            "A test custom field",
            False,
            "",
            json.dumps({"max_length": 50}),
            "product"
        ))
        
        field_id = cursor.lastrowid
        
        # Verify insertion
        cursor.execute("SELECT * FROM custom_field_definitions WHERE id = ?", (field_id,))
        field_data = cursor.fetchone()
        
        if field_data:
            print(f"✅ Custom field inserted: {field_data[2]} (ID: {field_id})")
        else:
            print("❌ Custom field insertion failed")
            return False
        
        # Update custom field
        cursor.execute("""
            UPDATE custom_field_definitions 
            SET display_name = ?, description = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, ("Updated Test Field", "Updated description", field_id))
        
        # Verify update
        cursor.execute("SELECT display_name, description FROM custom_field_definitions WHERE id = ?", (field_id,))
        updated_data = cursor.fetchone()
        
        if updated_data and updated_data[0] == "Updated Test Field":
            print(f"✅ Custom field updated: {updated_data[0]}")
        else:
            print("❌ Custom field update failed")
            return False
        
        # List all custom fields for store
        cursor.execute("""
            SELECT field_name, field_type, display_name, category
            FROM custom_field_definitions 
            WHERE store_id = ?
        """, (store_id,))
        
        fields = cursor.fetchall()
        print(f"✅ Custom fields for store: {len(fields)} fields")
        
        for field in fields:
            print(f"  - {field[2]} ({field[0]}): {field[1]} [{field[3]}]")
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """Main function"""
    print("🔄 Testing custom fields system...")
    
    tests = [
        ("Custom Fields API", test_custom_fields_api),
        ("Field Validation", test_custom_field_validation),
        ("Database Operations", test_custom_field_database)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"🧪 Testing {test_name}...")
        print(f"{'='*50}")
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} test passed")
        else:
            print(f"❌ {test_name} test failed")
    
    print(f"\n📊 Final Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All custom fields tests passed!")
        return 0
    else:
        print("\n❌ Some custom fields tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())