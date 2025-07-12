#!/usr/bin/env python3
"""
Automated test script for InventorySync app functionality
Tests all critical features before deployment
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3001"
SHOP_DOMAIN = "inventorysync-dev.myshopify.com"
AUTH_TOKEN = "dev-token"

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(test_name, status, message=""):
    """Print test result with color"""
    symbol = "✓" if status else "✗"
    color = GREEN if status else RED
    print(f"{color}{symbol} {test_name}{RESET} {message}")

def test_health_check():
    """Test API health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("status") == "healthy"
        return False
    except:
        return False

def test_custom_fields_api():
    """Test custom fields API endpoints"""
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    results = []
    
    # Test 1: Get templates
    try:
        response = requests.get(f"{BASE_URL}/api/custom-fields/templates", headers=headers)
        results.append(("Get templates", response.status_code == 200))
    except:
        results.append(("Get templates", False))
    
    # Test 2: Search fields
    try:
        response = requests.get(
            f"{BASE_URL}/api/custom-fields/search/{SHOP_DOMAIN}", 
            headers=headers
        )
        results.append(("Search fields", response.status_code == 200))
    except:
        results.append(("Search fields", False))
    
    # Test 3: Get statistics
    try:
        response = requests.get(
            f"{BASE_URL}/api/custom-fields/statistics/{SHOP_DOMAIN}", 
            headers=headers
        )
        results.append(("Get statistics", response.status_code == 200))
    except:
        results.append(("Get statistics", False))
    
    return results

def test_webhook_endpoints():
    """Test webhook endpoints"""
    results = []
    
    # Test product create webhook
    webhook_data = {
        "id": 123456,
        "title": "Test Product",
        "vendor": "Test Vendor",
        "product_type": "Test Type",
        "tags": ["test", "product"],
        "variants": [{
            "id": 789012,
            "title": "Default",
            "price": "19.99",
            "sku": "TEST-001"
        }]
    }
    
    headers = {
        "X-Shopify-Shop-Domain": SHOP_DOMAIN,
        "X-Shopify-Hmac-Sha256": "test-signature"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/webhooks/products/create",
            json=webhook_data,
            headers=headers
        )
        results.append(("Product create webhook", response.status_code == 200))
    except:
        results.append(("Product create webhook", False))
    
    return results

def test_database_connection():
    """Test database connectivity"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            return data.get("database") == "healthy"
        return False
    except:
        return False

def test_frontend_availability():
    """Test if frontend is accessible"""
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        return response.status_code == 200
    except:
        return False

def run_all_tests():
    """Run all tests and generate report"""
    print(f"\n{BLUE}=== InventorySync App Test Suite ==={RESET}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    all_passed = True
    
    # Test 1: Health check
    health_ok = test_health_check()
    print_test("API Health Check", health_ok)
    all_passed &= health_ok
    
    # Test 2: Database connection
    db_ok = test_database_connection()
    print_test("Database Connection", db_ok)
    all_passed &= db_ok
    
    # Test 3: Frontend availability
    frontend_ok = test_frontend_availability()
    print_test("Frontend Server", frontend_ok, f"({FRONTEND_URL})")
    all_passed &= frontend_ok
    
    # Test 4: Custom fields API
    print(f"\n{YELLOW}Custom Fields API Tests:{RESET}")
    api_results = test_custom_fields_api()
    for test_name, passed in api_results:
        print_test(f"  {test_name}", passed)
        all_passed &= passed
    
    # Test 5: Webhook endpoints
    print(f"\n{YELLOW}Webhook Tests:{RESET}")
    webhook_results = test_webhook_endpoints()
    for test_name, passed in webhook_results:
        print_test(f"  {test_name}", passed)
        all_passed &= passed
    
    # Summary
    print(f"\n{BLUE}=== Test Summary ==={RESET}")
    if all_passed:
        print(f"{GREEN}✓ All tests passed!{RESET}")
        print(f"\n{GREEN}The app is ready for deployment!{RESET}")
        return 0
    else:
        print(f"{RED}✗ Some tests failed!{RESET}")
        print(f"\n{YELLOW}Please fix the issues before deploying.{RESET}")
        return 1

if __name__ == "__main__":
    # Wait for servers to start
    print("Waiting for servers to start...")
    time.sleep(3)
    
    # Run tests
    exit_code = run_all_tests()
    sys.exit(exit_code)
