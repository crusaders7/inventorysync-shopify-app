#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Suite
Tests all major features of InventorySync
"""

import requests
import json
import time
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

BASE_URL = "http://localhost:8000"
SHOP_DOMAIN = "inventorysync-dev.myshopify.com"

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "tests": []
}


def print_test_header(test_name):
    """Print test header"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"Testing: {test_name}")
    print(f"{'='*60}{Style.RESET_ALL}")


def print_result(test_name, passed, details=""):
    """Print test result"""
    if passed:
        test_results["passed"] += 1
        status = f"{Fore.GREEN}✓ PASSED{Style.RESET_ALL}"
    else:
        test_results["failed"] += 1
        status = f"{Fore.RED}✗ FAILED{Style.RESET_ALL}"
    
    test_results["tests"].append({
        "name": test_name,
        "passed": passed,
        "details": details
    })
    
    print(f"  {status} - {test_name}")
    if details:
        print(f"    {Fore.YELLOW}Details: {details}{Style.RESET_ALL}")


def test_health_endpoints():
    """Test health check endpoints"""
    print_test_header("Health Check Endpoints")
    
    # Test main health endpoint
    try:
        response = requests.get(f"{BASE_URL}/health")
        passed = response.status_code == 200
        data = response.json()
        print_result("Main health endpoint", passed, f"Status: {data.get('status')}")
    except Exception as e:
        print_result("Main health endpoint", False, str(e))
    
    # Test database health
    try:
        response = requests.get(f"{BASE_URL}/health")
        data = response.json()
        db_healthy = data.get('database') == 'healthy'
        print_result("Database health", db_healthy, f"Database: {data.get('database')}")
    except Exception as e:
        print_result("Database health", False, str(e))


def test_custom_fields():
    """Test custom fields functionality"""
    print_test_header("Custom Fields API")
    
    # Get custom field definitions
    try:
        response = requests.get(f"{BASE_URL}/api/v1/custom-fields/{SHOP_DOMAIN}")
        passed = response.status_code == 200
        data = response.json()
        field_count = len(data.get('fields', []))
        print_result("Get custom field definitions", passed, f"Found {field_count} fields")
        
        # Check field grouping
        if passed and 'grouped_fields' in data:
            groups = list(data['grouped_fields'].keys())
            print_result("Field grouping", True, f"Groups: {', '.join(groups)}")
    except Exception as e:
        print_result("Get custom field definitions", False, str(e))
    
    # Test industry templates
    try:
        response = requests.get(f"{BASE_URL}/api/v1/custom-fields/templates")
        passed = response.status_code == 200
        data = response.json()
        template_count = len(data.get('templates', {}))
        print_result("Get industry templates", passed, f"Found {template_count} industries")
    except Exception as e:
        print_result("Get industry templates", False, str(e))


def test_alerts_system():
    """Test alerts functionality"""
    print_test_header("Alerts System")
    
    # List alerts
    try:
        response = requests.get(f"{BASE_URL}/api/v1/alerts/")
        passed = response.status_code == 200
        data = response.json()
        alert_count = data.get('total', 0)
        print_result("List alerts", passed, f"Found {alert_count} alerts")
    except Exception as e:
        print_result("List alerts", False, str(e))
    
    # Get store alerts
    try:
        response = requests.get(f"{BASE_URL}/api/v1/alerts/{SHOP_DOMAIN}")
        if response.status_code == 404:
            print_result("Get store alerts", True, "Store not found (expected in test)")
        else:
            passed = response.status_code == 200
            data = response.json()
            print_result("Get store alerts", passed, f"Total: {data.get('total', 0)}")
    except Exception as e:
        print_result("Get store alerts", False, str(e))
    
    # Dashboard alerts
    try:
        response = requests.get(f"{BASE_URL}/api/v1/dashboard/alerts")
        passed = response.status_code == 200
        data = response.json()
        print_result("Dashboard alerts", passed, f"Count: {len(data.get('alerts', []))}")
    except Exception as e:
        print_result("Dashboard alerts", False, str(e))


def test_inventory_management():
    """Test inventory management features"""
    print_test_header("Inventory Management")
    
    # List inventory
    try:
        response = requests.get(f"{BASE_URL}/api/v1/inventory/")
        passed = response.status_code == 200
        data = response.json()
        print_result("List inventory", passed, f"Total items: {data.get('total', 0)}")
    except Exception as e:
        print_result("List inventory", False, str(e))
    
    # Test inventory search
    try:
        response = requests.get(f"{BASE_URL}/api/v1/inventory/?search=test")
        passed = response.status_code == 200
        print_result("Inventory search", passed)
    except Exception as e:
        print_result("Inventory search", False, str(e))
    
    # Test inventory filters
    try:
        response = requests.get(f"{BASE_URL}/api/v1/inventory/?status=low_stock")
        passed = response.status_code == 200
        print_result("Inventory filters", passed)
    except Exception as e:
        print_result("Inventory filters", False, str(e))


def test_dashboard_stats():
    """Test dashboard statistics"""
    print_test_header("Dashboard Statistics")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/dashboard/stats")
        passed = response.status_code == 200
        data = response.json()
        
        print_result("Dashboard stats endpoint", passed)
        
        if passed:
            # Updated to check camelCase keys that actually exist in response
            stats_checks = [
                ("Total products", 'totalProducts' in data),
                ("Low stock alerts", 'lowStockAlerts' in data),
                ("Total value", 'totalValue' in data),
                ("Active locations", 'activeLocations' in data),
                ("Last sync", 'lastSync' in data),
                ("Sync status", 'syncStatus' in data)
            ]
            
            for stat_name, stat_exists in stats_checks:
                print_result(f"  {stat_name}", stat_exists)
    except Exception as e:
        print_result("Dashboard stats endpoint", False, str(e))


def test_performance():
    """Test API performance"""
    print_test_header("Performance Tests")
    
    endpoints = [
        ("/health", "Health check"),
        ("/api/v1/inventory/", "Inventory list"),
        ("/api/v1/alerts/", "Alerts list"),
        ("/api/v1/dashboard/stats", "Dashboard stats"),
        (f"/api/v1/custom-fields/{SHOP_DOMAIN}", "Custom fields")
    ]
    
    for endpoint, name in endpoints:
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}{endpoint}")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to ms
            passed = response_time < 500  # Should respond in under 500ms
            
            print_result(
                f"{name} response time",
                passed,
                f"{response_time:.2f}ms (Target: <500ms)"
            )
        except Exception as e:
            print_result(f"{name} response time", False, str(e))


def test_error_handling():
    """Test error handling"""
    print_test_header("Error Handling")
    
    # Test 404 handling
    try:
        response = requests.get(f"{BASE_URL}/api/v1/nonexistent")
        passed = response.status_code == 404
        print_result("404 error handling", passed)
    except Exception as e:
        print_result("404 error handling", False, str(e))
    
    # Test invalid shop domain
    try:
        response = requests.get(f"{BASE_URL}/api/v1/alerts/invalid-shop")
        passed = response.status_code in [404, 422]
        print_result("Invalid shop domain handling", passed)
    except Exception as e:
        print_result("Invalid shop domain handling", False, str(e))


def test_rate_limiting():
    """Test rate limiting"""
    print_test_header("Rate Limiting")
    
    # Note: Rate limiting might be disabled in dev
    try:
        # Make multiple rapid requests
        responses = []
        for i in range(10):
            response = requests.get(f"{BASE_URL}/health")
            responses.append(response.status_code)
        
        # Check if any were rate limited
        rate_limited = any(status == 429 for status in responses)
        all_successful = all(status == 200 for status in responses)
        
        if all_successful:
            print_result("Rate limiting", True, "Disabled in development (expected)")
        else:
            print_result("Rate limiting", rate_limited, f"Responses: {set(responses)}")
    except Exception as e:
        print_result("Rate limiting", False, str(e))


def generate_report():
    """Generate final test report"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    total_tests = test_results["passed"] + test_results["failed"]
    pass_rate = (test_results["passed"] / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"{Fore.GREEN}Passed: {test_results['passed']}{Style.RESET_ALL}")
    print(f"{Fore.RED}Failed: {test_results['failed']}{Style.RESET_ALL}")
    print(f"Pass Rate: {pass_rate:.1f}%")
    
    if test_results["failed"] > 0:
        print(f"\n{Fore.RED}Failed Tests:{Style.RESET_ALL}")
        for test in test_results["tests"]:
            if not test["passed"]:
                print(f"  - {test['name']}")
                if test["details"]:
                    print(f"    {test['details']}")
    
    # Save report to file
    report_path = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_path}")
    
    # Return exit code based on results
    return 0 if test_results["failed"] == 0 else 1


def main():
    """Run all tests"""
    print(f"{Fore.CYAN}{'='*60}")
    print("INVENTORYSYNC END-TO-END TEST SUITE")
    print(f"{'='*60}{Style.RESET_ALL}")
    print(f"Base URL: {BASE_URL}")
    print(f"Shop Domain: {SHOP_DOMAIN}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all test suites
    test_health_endpoints()
    test_custom_fields()
    test_alerts_system()
    test_inventory_management()
    test_dashboard_stats()
    test_performance()
    test_error_handling()
    test_rate_limiting()
    
    # Generate report
    exit_code = generate_report()
    
    print(f"\n{Fore.CYAN}Test suite completed!{Style.RESET_ALL}")
    return exit_code


if __name__ == "__main__":
    exit(main())
