#!/usr/bin/env python3
"""
Comprehensive endpoint testing script for InventorySync Shopify App
"""
import requests
import json
import sys
from typing import Dict, List, Tuple
import os
from datetime import datetime

# Configuration
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
SHOPIFY_SHOP_DOMAIN = "test-shop.myshopify.com"
ACCESS_TOKEN = "test_access_token"

class APITester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.results = []
        
    def test_endpoint(self, method: str, path: str, data: Dict = None, 
                     headers: Dict = None, expected_status: int = 200) -> Tuple[bool, Dict]:
        """Test a single endpoint"""
        url = f"{self.base_url}{path}"
        default_headers = {
            "Content-Type": "application/json",
            "X-Shopify-Shop-Domain": SHOPIFY_SHOP_DOMAIN,
            "X-Shopify-Access-Token": ACCESS_TOKEN
        }
        
        if headers:
            default_headers.update(headers)
            
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                headers=default_headers,
                timeout=10,
                allow_redirects=False  # Don't follow redirects automatically
            )
            
            success = response.status_code == expected_status
            
            # Handle response content based on status code
            response_data = None
            if response.content:
                try:
                    response_data = response.json()
                except:
                    # Not JSON content (like redirects)
                    response_data = {"redirect": response.headers.get("Location", "")} if response.status_code in [301, 302, 307] else None
            
            result = {
                "endpoint": f"{method} {path}",
                "status_code": response.status_code,
                "expected_status": expected_status,
                "success": success,
                "response": response_data,
                "error": None
            }
            
        except Exception as e:
            success = False
            result = {
                "endpoint": f"{method} {path}",
                "status_code": None,
                "expected_status": expected_status,
                "success": False,
                "response": None,
                "error": str(e)
            }
            
        self.results.append(result)
        return success, result
    
    def run_all_tests(self):
        """Run comprehensive endpoint tests"""
        print("🧪 Starting Comprehensive Endpoint Testing...")
        print(f"Base URL: {self.base_url}\n")
        
        # Basic Health Checks
        print("1️⃣ Testing Basic Health Endpoints:")
        self.test_endpoint("GET", "/")
        self.test_endpoint("GET", "/health")
        self.test_endpoint("GET", "/api")
        
        # Authentication
        print("\n2️⃣ Testing Authentication:")
        self.test_endpoint("GET", "/api/auth/install?shop=test-shop.myshopify.com", expected_status=307)
        self.test_endpoint("GET", "/api/auth/callback", expected_status=422)
        
        # Inventory Management
        print("\n3️⃣ Testing Inventory Management:")
        self.test_endpoint("GET", "/api/inventory/items")
        self.test_endpoint("GET", "/api/inventory/levels")
        self.test_endpoint("POST", "/api/inventory/sync", data={})
        self.test_endpoint("GET", "/api/inventory/history")
        
        # Locations
        print("\n4️⃣ Testing Location Management:")
        self.test_endpoint("GET", "/api/locations/")
        self.test_endpoint("POST", "/api/locations/", data={
            "name": "Test Location",
            "address": "123 Test St",
            "is_active": True
        })
        
        # Alerts
        print("\n5️⃣ Testing Alerts:")
        self.test_endpoint("GET", "/api/alerts/")
        self.test_endpoint("POST", "/api/alerts/", data={
            "type": "low_stock",
            "threshold": 10,
            "is_active": True
        })
        
        # Webhooks
        print("\n6️⃣ Testing Webhooks:")
        self.test_endpoint("GET", "/api/webhooks/")
        self.test_endpoint("POST", "/api/webhooks/register", data={
            "topic": "inventory_levels/update"
        })
        
        # Reports
        print("\n7️⃣ Testing Reports:")
        self.test_endpoint("GET", "/api/reports/inventory-summary")
        self.test_endpoint("GET", "/api/reports/movement-history")
        self.test_endpoint("GET", "/api/reports/low-stock")
        
        # Forecasting
        print("\n8️⃣ Testing Forecasting:")
        self.test_endpoint("GET", "/api/forecasting/demand")
        self.test_endpoint("POST", "/api/forecasting/generate")
        
        # Workflows
        print("\n9️⃣ Testing Workflows:")
        self.test_endpoint("GET", "/api/workflows/")
        self.test_endpoint("POST", "/api/workflows/", data={
            "name": "Test Workflow",
            "trigger": "low_stock",
            "actions": []
        })
        
        # GDPR Compliance
        print("\n🔟 Testing GDPR Endpoints:")
        self.test_endpoint("POST", "/api/webhooks/customers/data_request", 
                          data={"shop_domain": SHOPIFY_SHOP_DOMAIN})
        self.test_endpoint("POST", "/api/webhooks/customers/redact", 
                          data={"shop_domain": SHOPIFY_SHOP_DOMAIN})
        self.test_endpoint("POST", "/api/webhooks/shop/redact", 
                          data={"shop_domain": SHOPIFY_SHOP_DOMAIN})
        
        # Generate Report
        self.generate_report()
        
    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*60)
        print("📊 TEST RESULTS SUMMARY")
        print("="*60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if not result["success"]:
                    print(f"\n- {result['endpoint']}")
                    print(f"  Expected: {result['expected_status']}, Got: {result['status_code']}")
                    if result["error"]:
                        print(f"  Error: {result['error']}")
                        
        # Save detailed report
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Detailed report saved to: {report_file}")

def check_shopify_requirements():
    """Check if app meets Shopify marketplace requirements"""
    print("\n" + "="*60)
    print("🛍️ SHOPIFY MARKETPLACE READINESS CHECK")
    print("="*60)
    
    requirements = {
        "GDPR Webhooks": False,
        "OAuth Implementation": False,
        "Billing API": False,
        "App Bridge Support": False,
        "Webhook Verification": False,
        "Rate Limiting": False,
        "Error Handling": False,
        "Security Headers": False,
        "HTTPS Support": False,
        "Session Token Auth": False
    }
    
    # Check implementation files
    if os.path.exists("/home/brend/inventorysync-shopify-app/backend/api/gdpr.py"):
        requirements["GDPR Webhooks"] = True
    
    if os.path.exists("/home/brend/inventorysync-shopify-app/backend/api/auth.py"):
        requirements["OAuth Implementation"] = True
        
    if os.path.exists("/home/brend/inventorysync-shopify-app/backend/api/billing.py"):
        requirements["Billing API"] = True
        
    # TODO: Add more checks
    
    print("\nRequirements Status:")
    for req, status in requirements.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {req}")
        
    ready = all(requirements.values())
    print(f"\n{'✅ App is ready for Shopify marketplace!' if ready else '❌ App needs more work before marketplace submission'}")
    
    return requirements

if __name__ == "__main__":
    # Run tests
    tester = APITester(BASE_URL)
    
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ Server is running at {BASE_URL}")
    except:
        print(f"❌ Server is not accessible at {BASE_URL}")
        print("Please ensure the server is running and try again.")
        sys.exit(1)
    
    # Run endpoint tests
    tester.run_all_tests()
    
    # Check Shopify requirements
    requirements = check_shopify_requirements()
    
    print("\n📝 NEXT STEPS:")
    print("1. Fix any failing endpoints")
    print("2. Implement missing Shopify requirements")
    print("3. Add comprehensive error handling")
    print("4. Implement rate limiting")
    print("5. Add request/response logging")
    print("6. Set up monitoring and alerts")
    print("7. Perform security audit")
    print("8. Create user documentation")
