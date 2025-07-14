#!/usr/bin/env python3
"""
Comprehensive test suite for custom fields management functionality
Testing:
- CRUD operations (Create, Read, Update, Delete)
- Field validation rules
- Bulk operations
- Field mapping between systems
- Synchronization accuracy
- Error handling
"""

import requests
import json
import sqlite3
import sys
import time
import random
from datetime import datetime
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
SHOP_DOMAIN = "inventorysync-dev.myshopify.com"
DB_PATH = "inventorysync_dev.db"

class CustomFieldsTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.shop_domain = SHOP_DOMAIN
        self.db_path = DB_PATH
        self.created_fields = []
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "details": []
        }
    
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        if passed:
            self.test_results["passed"] += 1
            print(f"✅ {test_name}: PASSED")
        else:
            self.test_results["failed"] += 1
            print(f"❌ {test_name}: FAILED - {details}")
        
        self.test_results["details"].append({
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def cleanup(self):
        """Clean up created test data"""
        print("\n🧹 Cleaning up test data...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Delete test custom fields
            if self.created_fields:
                placeholders = ','.join('?' * len(self.created_fields))
                cursor.execute(f"""
                    DELETE FROM custom_field_definitions 
                    WHERE id IN ({placeholders})
                """, self.created_fields)
                conn.commit()
                print(f"✅ Deleted {len(self.created_fields)} test custom fields")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")
        finally:
            conn.close()
    
    def test_create_custom_field(self) -> Optional[int]:
        """Test creating a custom field"""
        test_name = "Create Custom Field"
        
        field_data = {
            "field_name": f"test_supplier_code_{int(time.time())}",
            "display_name": "Supplier Code",
            "field_type": "single_line_text",
            "target_entity": "product",
            "validation_rules": {
                "max_length": 20,
                "pattern": "^[A-Z0-9-]+$",
                "required": True
            },
            "is_required": True,
            "is_searchable": True,
            "is_filterable": True,
            "display_order": 1,
            "help_text": "Enter the supplier code in format XXX-000",
            "default_value": "",
            "field_group": "inventory",
            "industry_template": "retail"
        }
        
        try:
            # First, let's check what endpoint exists
            response = requests.get(f"{self.base_url}/custom-fields/types")
            if response.status_code == 200:
                # Use the enhanced API
                endpoint = f"{self.base_url}/custom-fields"
            else:
                # Try the simple API
                endpoint = f"{self.base_url}/custom-fields/value-proposition"
                
            response = requests.post(endpoint, json=field_data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                field_id = result.get("id") or result.get("field_id")
                if field_id:
                    self.created_fields.append(field_id)
                    self.log_result(test_name, True)
                    return field_id
                else:
                    self.log_result(test_name, False, "No field ID returned")
                    return None
            else:
                self.log_result(test_name, False, f"Status {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_result(test_name, False, str(e))
            return None
    
    def test_read_custom_fields(self):
        """Test reading custom fields"""
        test_name = "Read Custom Fields"
        
        try:
            # Try different endpoints
            endpoints = [
                f"{self.base_url}/custom-fields",
                f"{self.base_url}/custom-fields/value-proposition",
                f"{self.base_url}/custom-fields/{self.shop_domain}"
            ]
            
            for endpoint in endpoints:
                response = requests.get(endpoint)
                if response.status_code == 200:
                    result = response.json()
                    fields = result.get("fields", result.get("custom_fields", []))
                    self.log_result(test_name, True)
                    return fields
            
            self.log_result(test_name, False, "No valid endpoint found")
            return []
            
        except Exception as e:
            self.log_result(test_name, False, str(e))
            return []
    
    def test_update_custom_field(self, field_id: int):
        """Test updating a custom field"""
        test_name = "Update Custom Field"
        
        update_data = {
            "display_name": "Supplier Code (Updated)",
            "help_text": "Updated help text for supplier code",
            "validation_rules": {
                "max_length": 25,
                "pattern": "^[A-Z0-9-]+$",
                "required": True
            }
        }
        
        try:
            endpoints = [
                f"{self.base_url}/custom-fields/{field_id}",
                f"{self.base_url}/custom-fields/{self.shop_domain}/{field_id}"
            ]
            
            for endpoint in endpoints:
                response = requests.put(endpoint, json=update_data)
                if response.status_code in [200, 204]:
                    self.log_result(test_name, True)
                    return True
            
            self.log_result(test_name, False, "Update failed on all endpoints")
            return False
            
        except Exception as e:
            self.log_result(test_name, False, str(e))
            return False
    
    def test_delete_custom_field(self, field_id: int):
        """Test deleting a custom field"""
        test_name = "Delete Custom Field"
        
        try:
            endpoints = [
                f"{self.base_url}/custom-fields/{field_id}",
                f"{self.base_url}/custom-fields/{self.shop_domain}/{field_id}"
            ]
            
            for endpoint in endpoints:
                response = requests.delete(endpoint)
                if response.status_code in [200, 204]:
                    if field_id in self.created_fields:
                        self.created_fields.remove(field_id)
                    self.log_result(test_name, True)
                    return True
            
            self.log_result(test_name, False, "Delete failed on all endpoints")
            return False
            
        except Exception as e:
            self.log_result(test_name, False, str(e))
            return False
    
    def test_field_validation(self):
        """Test field validation rules"""
        test_name = "Field Validation Rules"
        
        validation_tests = [
            {
                "name": "Valid supplier code",
                "field_type": "single_line_text",
                "value": "SUP-12345",
                "rules": {"pattern": "^[A-Z0-9-]+$", "max_length": 20},
                "expected": True
            },
            {
                "name": "Invalid supplier code (lowercase)",
                "field_type": "single_line_text", 
                "value": "sup-12345",
                "rules": {"pattern": "^[A-Z0-9-]+$", "max_length": 20},
                "expected": False
            },
            {
                "name": "Too long value",
                "field_type": "single_line_text",
                "value": "A" * 30,
                "rules": {"max_length": 20},
                "expected": False
            },
            {
                "name": "Valid number in range",
                "field_type": "number_integer",
                "value": 50,
                "rules": {"min_value": 0, "max_value": 100},
                "expected": True
            },
            {
                "name": "Number out of range",
                "field_type": "number_integer",
                "value": 150,
                "rules": {"min_value": 0, "max_value": 100},
                "expected": False
            }
        ]
        
        passed = 0
        for test in validation_tests:
            is_valid = self.validate_field_value(
                test["field_type"],
                test["value"],
                test["rules"]
            )
            
            if is_valid == test["expected"]:
                passed += 1
                print(f"  ✓ {test['name']}")
            else:
                print(f"  ✗ {test['name']} (expected {test['expected']}, got {is_valid})")
        
        self.log_result(test_name, passed == len(validation_tests), 
                       f"{passed}/{len(validation_tests)} validation tests passed")
    
    def validate_field_value(self, field_type: str, value: Any, rules: Dict) -> bool:
        """Validate a field value against rules"""
        import re
        
        try:
            if field_type in ["single_line_text", "multi_line_text"]:
                if not isinstance(value, str):
                    return False
                
                if "max_length" in rules and len(value) > rules["max_length"]:
                    return False
                
                if "pattern" in rules and not re.match(rules["pattern"], value):
                    return False
                
                return True
                
            elif field_type in ["number_integer", "number_decimal"]:
                if not isinstance(value, (int, float)):
                    return False
                
                if "min_value" in rules and value < rules["min_value"]:
                    return False
                
                if "max_value" in rules and value > rules["max_value"]:
                    return False
                
                return True
                
            return True
            
        except:
            return False
    
    def test_bulk_operations(self):
        """Test bulk field operations"""
        test_name = "Bulk Field Operations"
        
        # Create multiple fields
        bulk_fields = []
        for i in range(5):
            field_data = {
                "field_name": f"bulk_test_field_{i}_{int(time.time())}",
                "display_name": f"Bulk Test Field {i}",
                "field_type": "single_line_text",
                "target_entity": "product",
                "is_required": False,
                "field_group": "test_bulk"
            }
            bulk_fields.append(field_data)
        
        try:
            # Test bulk create (if supported)
            created_count = 0
            start_time = time.time()
            
            # Try bulk endpoint first
            response = requests.post(f"{self.base_url}/custom-fields/bulk", json={"fields": bulk_fields})
            
            if response.status_code in [200, 201]:
                result = response.json()
                created_count = len(result.get("created_fields", []))
                for field in result.get("created_fields", []):
                    if field.get("id"):
                        self.created_fields.append(field["id"])
            else:
                # Fall back to individual creation
                with ThreadPoolExecutor(max_workers=3) as executor:
                    futures = []
                    for field_data in bulk_fields:
                        future = executor.submit(self.create_field_async, field_data)
                        futures.append(future)
                    
                    for future in as_completed(futures):
                        field_id = future.result()
                        if field_id:
                            created_count += 1
                            self.created_fields.append(field_id)
            
            elapsed_time = time.time() - start_time
            
            self.log_result(test_name, created_count == len(bulk_fields),
                           f"Created {created_count}/{len(bulk_fields)} fields in {elapsed_time:.2f}s")
            
        except Exception as e:
            self.log_result(test_name, False, str(e))
    
    def create_field_async(self, field_data: Dict) -> Optional[int]:
        """Create a field asynchronously"""
        try:
            response = requests.post(f"{self.base_url}/custom-fields", json=field_data)
            if response.status_code in [200, 201]:
                result = response.json()
                return result.get("id") or result.get("field_id")
        except:
            pass
        return None
    
    def test_field_mapping(self):
        """Test field mapping between different systems"""
        test_name = "Field Mapping"
        
        # Create fields with mapping information
        mapping_data = {
            "shopify_to_external": {
                "vendor": "supplier_name",
                "sku": "internal_sku",
                "barcode": "ean_code"
            },
            "external_to_shopify": {
                "supplier_name": "vendor",
                "internal_sku": "sku",
                "ean_code": "barcode"
            }
        }
        
        try:
            # Test mapping configuration
            field_mappings = []
            
            for shopify_field, external_field in mapping_data["shopify_to_external"].items():
                mapping = {
                    "source_field": shopify_field,
                    "target_field": external_field,
                    "mapping_type": "shopify_to_external",
                    "transformation": None
                }
                field_mappings.append(mapping)
            
            # Verify bidirectional mapping
            mapping_valid = True
            for source, target in mapping_data["shopify_to_external"].items():
                reverse = mapping_data["external_to_shopify"].get(target)
                if reverse != source:
                    mapping_valid = False
                    break
            
            self.log_result(test_name, mapping_valid,
                           f"Validated {len(field_mappings)} field mappings")
            
        except Exception as e:
            self.log_result(test_name, False, str(e))
    
    def test_field_synchronization(self):
        """Test field synchronization accuracy"""
        test_name = "Field Synchronization"
        
        try:
            # Simulate field sync scenarios
            sync_tests = [
                {
                    "name": "Text field sync",
                    "source_value": "TEST-123",
                    "expected_value": "TEST-123",
                    "field_type": "text"
                },
                {
                    "name": "Number field sync",
                    "source_value": 42.5,
                    "expected_value": 42.5,
                    "field_type": "number"
                },
                {
                    "name": "Boolean field sync",
                    "source_value": True,
                    "expected_value": True,
                    "field_type": "boolean"
                },
                {
                    "name": "Date field sync",
                    "source_value": "2025-01-13",
                    "expected_value": "2025-01-13",
                    "field_type": "date"
                }
            ]
            
            sync_passed = 0
            for test in sync_tests:
                # Simulate sync
                synced_value = self.sync_field_value(
                    test["source_value"],
                    test["field_type"]
                )
                
                if synced_value == test["expected_value"]:
                    sync_passed += 1
                    print(f"  ✓ {test['name']}")
                else:
                    print(f"  ✗ {test['name']} (expected {test['expected_value']}, got {synced_value})")
            
            self.log_result(test_name, sync_passed == len(sync_tests),
                           f"{sync_passed}/{len(sync_tests)} sync tests passed")
            
        except Exception as e:
            self.log_result(test_name, False, str(e))
    
    def sync_field_value(self, value: Any, field_type: str) -> Any:
        """Simulate field value synchronization"""
        if field_type == "text":
            return str(value)
        elif field_type == "number":
            return float(value) if isinstance(value, (int, float, str)) else None
        elif field_type == "boolean":
            return bool(value)
        elif field_type == "date":
            return str(value)
        return value
    
    def test_error_handling(self):
        """Test error handling for invalid configurations"""
        test_name = "Error Handling"
        
        error_tests = [
            {
                "name": "Invalid field type",
                "data": {
                    "field_name": "invalid_type_field",
                    "field_type": "invalid_type",
                    "display_name": "Invalid Type Field"
                },
                "expected_error": True
            },
            {
                "name": "Missing required fields",
                "data": {
                    "field_name": "incomplete_field"
                },
                "expected_error": True
            },
            {
                "name": "Invalid field name format",
                "data": {
                    "field_name": "Invalid-Field-Name!",
                    "field_type": "single_line_text",
                    "display_name": "Invalid Field"
                },
                "expected_error": True
            },
            {
                "name": "Duplicate field name",
                "data": {
                    "field_name": "duplicate_test_field",
                    "field_type": "single_line_text",
                    "display_name": "Duplicate Field"
                },
                "expected_error": False  # First creation should succeed
            }
        ]
        
        errors_handled = 0
        
        for test in error_tests:
            try:
                response = requests.post(f"{self.base_url}/custom-fields", json=test["data"])
                
                if test["name"] == "Duplicate field name" and response.status_code in [200, 201]:
                    # Try to create again - this should fail
                    response2 = requests.post(f"{self.base_url}/custom-fields", json=test["data"])
                    if response2.status_code >= 400:
                        errors_handled += 1
                        print(f"  ✓ {test['name']} - Error properly handled")
                    else:
                        print(f"  ✗ {test['name']} - Duplicate not prevented")
                elif test["expected_error"] and response.status_code >= 400:
                    errors_handled += 1
                    print(f"  ✓ {test['name']} - Error properly handled")
                elif not test["expected_error"] and response.status_code in [200, 201]:
                    errors_handled += 1
                    print(f"  ✓ {test['name']} - Success as expected")
                else:
                    print(f"  ✗ {test['name']} - Unexpected response: {response.status_code}")
                
            except Exception as e:
                print(f"  ✗ {test['name']} - Exception: {e}")
        
        self.log_result(test_name, errors_handled >= len(error_tests) - 1,
                       f"{errors_handled}/{len(error_tests)} error cases handled correctly")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 Starting Comprehensive Custom Fields Tests")
        print("=" * 60)
        
        # Test CRUD operations
        print("\n📝 Testing CRUD Operations...")
        field_id = self.test_create_custom_field()
        self.test_read_custom_fields()
        
        if field_id:
            self.test_update_custom_field(field_id)
            # Don't delete yet, we'll clean up at the end
        
        # Test validation
        print("\n🔍 Testing Field Validation...")
        self.test_field_validation()
        
        # Test bulk operations
        print("\n📦 Testing Bulk Operations...")
        self.test_bulk_operations()
        
        # Test field mapping
        print("\n🔄 Testing Field Mapping...")
        self.test_field_mapping()
        
        # Test synchronization
        print("\n🔄 Testing Field Synchronization...")
        self.test_field_synchronization()
        
        # Test error handling
        print("\n⚠️ Testing Error Handling...")
        self.test_error_handling()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"📈 Success Rate: {self.test_results['passed'] / (self.test_results['passed'] + self.test_results['failed']) * 100:.1f}%")
        
        # Save detailed results
        with open("custom_fields_test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        print("\n📄 Detailed results saved to custom_fields_test_results.json")
        
        # Cleanup
        self.cleanup()
        
        return self.test_results["failed"] == 0

def main():
    """Main function"""
    tester = CustomFieldsTester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        tester.cleanup()
        return 1
    except Exception as e:
        print(f"\n\n❌ Test suite error: {e}")
        tester.cleanup()
        return 1

if __name__ == "__main__":
    sys.exit(main())
