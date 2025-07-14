#!/usr/bin/env python3
"""
Test suite for the actual custom fields API implementation
"""

import requests
import json
import sqlite3
import sys
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configuration
BASE_URL = "http://localhost:8000/api/custom-fields"
SHOP_DOMAIN = "inventorysync-dev.myshopify.com"

class CustomFieldsActualTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.shop_domain = SHOP_DOMAIN
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
    
    def test_create_custom_field(self) -> Optional[str]:
        """Test creating a custom field"""
        test_name = "Create Custom Field"
        
        field_data = {
            "field_name": f"test_supplier_code_{int(time.time())}",
            "display_name": "Supplier Code",
            "field_type": "text",
            "target_entity": "product",
            "validation_rules": {
                "max_length": 20,
                "pattern": "^[A-Z0-9-]+$"
            },
            "is_required": True
        }
        
        try:
            response = requests.post(f"{self.base_url}/{self.shop_domain}", json=field_data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                field = result.get("field", {})
                field_id = field.get("id")
                
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
            # Test shop-specific fields
            response = requests.get(f"{self.base_url}/{self.shop_domain}")
            if response.status_code == 200:
                result = response.json()
                fields = result.get("fields", [])
                self.log_result(test_name, True)
                return fields
            else:
                self.log_result(test_name, False, f"Status {response.status_code}")
                return []
            
        except Exception as e:
            self.log_result(test_name, False, str(e))
            return []
    
    def test_list_all_fields(self):
        """Test listing all custom fields"""
        test_name = "List All Fields"
        
        try:
            response = requests.get(f"{self.base_url}/")
            if response.status_code == 200:
                result = response.json()
                total = result.get("total", 0)
                self.log_result(test_name, True)
                return result
            else:
                self.log_result(test_name, False, f"Status {response.status_code}")
                return {}
            
        except Exception as e:
            self.log_result(test_name, False, str(e))
            return {}
    
    def test_delete_custom_field(self, field_id: str):
        """Test deleting a custom field"""
        test_name = "Delete Custom Field"
        
        try:
            response = requests.delete(f"{self.base_url}/{self.shop_domain}/{field_id}")
            
            if response.status_code in [200, 204]:
                if field_id in self.created_fields:
                    self.created_fields.remove(field_id)
                self.log_result(test_name, True)
                return True
            else:
                self.log_result(test_name, False, f"Status {response.status_code}")
                return False
            
        except Exception as e:
            self.log_result(test_name, False, str(e))
            return False
    
    def test_value_proposition(self):
        """Test value proposition endpoint"""
        test_name = "Value Proposition"
        
        try:
            response = requests.get(f"{self.base_url}/value-proposition")
            if response.status_code == 200:
                result = response.json()
                
                # Verify key value props are present
                checks = [
                    "feature" in result,
                    "our_price" in result,
                    "shopify_plus_price" in result,
                    "monthly_savings" in result,
                    "benefits" in result and len(result["benefits"]) > 0,
                    "use_cases" in result and len(result["use_cases"]) > 0
                ]
                
                if all(checks):
                    self.log_result(test_name, True)
                    print(f"  💰 Monthly savings: {result.get('monthly_savings')}")
                    print(f"  💰 Annual savings: {result.get('annual_savings')}")
                else:
                    self.log_result(test_name, False, "Missing value proposition data")
            else:
                self.log_result(test_name, False, f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result(test_name, False, str(e))
    
    def test_field_templates(self):
        """Test field templates"""
        test_name = "Field Templates"
        
        try:
            response = requests.get(f"{self.base_url}/templates")
            if response.status_code == 200:
                result = response.json()
                templates = result.get("templates", {})
                
                # Verify templates for different industries
                expected_industries = ["apparel", "electronics", "food_beverage", "jewelry"]
                found_industries = list(templates.keys())
                
                if all(industry in found_industries for industry in expected_industries):
                    self.log_result(test_name, True)
                    print(f"  📋 Found {len(found_industries)} industry templates")
                else:
                    self.log_result(test_name, False, f"Missing some templates. Found: {found_industries}")
            else:
                self.log_result(test_name, False, f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result(test_name, False, str(e))
    
    def test_apply_template(self):
        """Test applying a template"""
        test_name = "Apply Template"
        
        try:
            # Apply apparel template
            response = requests.post(f"{self.base_url}/templates/apparel/apply/{self.shop_domain}")
            
            if response.status_code == 200:
                result = response.json()
                fields_created = result.get("fields_created", 0)
                
                if fields_created > 0:
                    self.log_result(test_name, True)
                    print(f"  📋 Created {fields_created} fields from template")
                    print(f"  💰 Monthly savings: {result.get('monthly_savings')}")
                else:
                    self.log_result(test_name, False, "No fields created")
            else:
                self.log_result(test_name, False, f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result(test_name, False, str(e))
    
    def test_field_validation_rules(self):
        """Test field validation with different data types"""
        test_name = "Field Validation Rules"
        
        test_fields = [
            {
                "name": "Text field with pattern",
                "data": {
                    "field_name": f"pattern_field_{int(time.time())}",
                    "display_name": "Pattern Test",
                    "field_type": "text",
                    "validation_rules": {
                        "pattern": "^[A-Z]{3}-[0-9]{3}$",
                        "max_length": 7
                    }
                }
            },
            {
                "name": "Number field",
                "data": {
                    "field_name": f"number_field_{int(time.time())}",
                    "display_name": "Quantity",
                    "field_type": "number",
                    "validation_rules": {
                        "min_value": 0,
                        "max_value": 1000
                    }
                }
            },
            {
                "name": "Date field",
                "data": {
                    "field_name": f"date_field_{int(time.time())}",
                    "display_name": "Expiry Date",
                    "field_type": "date"
                }
            },
            {
                "name": "Select field",
                "data": {
                    "field_name": f"select_field_{int(time.time())}",
                    "display_name": "Size",
                    "field_type": "select",
                    "options": ["S", "M", "L", "XL"]
                }
            }
        ]
        
        created_count = 0
        for field_test in test_fields:
            try:
                response = requests.post(f"{self.base_url}/{self.shop_domain}", json=field_test["data"])
                if response.status_code in [200, 201]:
                    created_count += 1
                    result = response.json()
                    field_id = result.get("field", {}).get("id")
                    if field_id:
                        self.created_fields.append(field_id)
                    print(f"  ✓ {field_test['name']} created")
                else:
                    print(f"  ✗ {field_test['name']} failed: {response.status_code}")
            except Exception as e:
                print(f"  ✗ {field_test['name']} error: {e}")
        
        self.log_result(test_name, created_count == len(test_fields), 
                       f"Created {created_count}/{len(test_fields)} validation test fields")
    
    def test_bulk_operations(self):
        """Test creating multiple fields quickly"""
        test_name = "Bulk Operations Performance"
        
        start_time = time.time()
        fields_to_create = 10
        created_count = 0
        
        for i in range(fields_to_create):
            field_data = {
                "field_name": f"bulk_field_{i}_{int(time.time())}",
                "display_name": f"Bulk Field {i}",
                "field_type": "text"
            }
            
            try:
                response = requests.post(f"{self.base_url}/{self.shop_domain}", json=field_data)
                if response.status_code in [200, 201]:
                    created_count += 1
                    result = response.json()
                    field_id = result.get("field", {}).get("id")
                    if field_id:
                        self.created_fields.append(field_id)
            except:
                pass
        
        elapsed_time = time.time() - start_time
        avg_time = elapsed_time / fields_to_create if fields_to_create > 0 else 0
        
        self.log_result(test_name, created_count == fields_to_create,
                       f"Created {created_count}/{fields_to_create} in {elapsed_time:.2f}s (avg: {avg_time:.3f}s/field)")
    
    def test_error_handling(self):
        """Test error handling"""
        test_name = "Error Handling"
        
        error_tests = [
            {
                "name": "Missing required field",
                "data": {"field_type": "text"},
                "expected_status": [400, 422]
            },
            {
                "name": "Invalid template",
                "endpoint": f"/templates/invalid_template/apply/{self.shop_domain}",
                "method": "POST",
                "expected_status": [404]
            },
            {
                "name": "Delete non-existent field",
                "endpoint": f"/{self.shop_domain}/non_existent_field_123",
                "method": "DELETE",
                "expected_status": [404]
            }
        ]
        
        errors_handled = 0
        for test in error_tests:
            try:
                if test.get("method") == "POST":
                    response = requests.post(f"{self.base_url}{test['endpoint']}")
                elif test.get("method") == "DELETE":
                    response = requests.delete(f"{self.base_url}{test['endpoint']}")
                else:
                    response = requests.post(f"{self.base_url}/{self.shop_domain}", json=test["data"])
                
                if response.status_code in test.get("expected_status", [400, 404, 422]):
                    errors_handled += 1
                    print(f"  ✓ {test['name']} - Error handled correctly ({response.status_code})")
                else:
                    print(f"  ✗ {test['name']} - Unexpected status: {response.status_code}")
            except Exception as e:
                print(f"  ✗ {test['name']} - Exception: {e}")
        
        self.log_result(test_name, errors_handled == len(error_tests),
                       f"{errors_handled}/{len(error_tests)} error cases handled correctly")
    
    def cleanup(self):
        """Clean up created fields"""
        if self.created_fields:
            print(f"\n🧹 Cleaning up {len(self.created_fields)} test fields...")
            cleaned = 0
            for field_id in self.created_fields[:]:
                try:
                    response = requests.delete(f"{self.base_url}/{self.shop_domain}/{field_id}")
                    if response.status_code in [200, 204]:
                        cleaned += 1
                        self.created_fields.remove(field_id)
                except:
                    pass
            print(f"✅ Cleaned up {cleaned} fields")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 Testing Custom Fields Management System")
        print("=" * 60)
        
        # Test basic CRUD
        print("\n📝 Testing CRUD Operations...")
        field_id = self.test_create_custom_field()
        self.test_read_custom_fields()
        self.test_list_all_fields()
        if field_id:
            self.test_delete_custom_field(field_id)
        
        # Test value proposition
        print("\n💰 Testing Value Proposition...")
        self.test_value_proposition()
        
        # Test templates
        print("\n📋 Testing Templates...")
        self.test_field_templates()
        self.test_apply_template()
        
        # Test validation
        print("\n🔍 Testing Field Validation...")
        self.test_field_validation_rules()
        
        # Test performance
        print("\n⚡ Testing Bulk Operations...")
        self.test_bulk_operations()
        
        # Test error handling
        print("\n⚠️ Testing Error Handling...")
        self.test_error_handling()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        total_tests = self.test_results['passed'] + self.test_results['failed']
        if total_tests > 0:
            success_rate = (self.test_results['passed'] / total_tests) * 100
            print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Save results
        with open("custom_fields_actual_test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        print("\n📄 Detailed results saved to custom_fields_actual_test_results.json")
        
        # Cleanup
        self.cleanup()
        
        return self.test_results["failed"] == 0

def main():
    """Main function"""
    tester = CustomFieldsActualTester()
    
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
