#!/usr/bin/env python3
"""
Comprehensive testing script for all InventorySync API endpoints
"""

import requests
import json
import time
from datetime import datetime
import sys

# Configuration
BASE_URL = "https://inventorysync-production.up.railway.app"
TEST_SHOP = "test-shop.myshopify.com"
ADMIN_TOKEN = "test-admin-token"  # Replace with actual admin token

# Test results tracking
results = {
    "passed": 0,
    "failed": 0,
    "warnings": 0,
    "start_time": datetime.now(),
    "tests": []
}

def print_header(text):
    print(f"\n{'='*60}")
    print(f" {text}")
    print(f"{'='*60}")

def test_endpoint(name, method, path, **kwargs):
    """Test a single endpoint"""
    global results
    
    print(f"\n[TEST] {name}")
    print(f"  {method} {path}")
    
    try:
        url = f"{BASE_URL}{path}"
        response = requests.request(method, url, **kwargs)
        
        test_result = {
            "name": name,
            "endpoint": f"{method} {path}",
            "status_code": response.status_code,
            "response_time": response.elapsed.total_seconds(),
            "timestamp": datetime.now().isoformat()
        }
        
        if response.status_code < 400:
            print(f"  ✅ Status: {response.status_code}")
            print(f"  ⏱️  Response time: {response.elapsed.total_seconds():.3f}s")
            
            # Try to parse JSON response
            try:
                data = response.json()
                print(f"  📦 Response: {json.dumps(data, indent=2)[:200]}...")
                test_result["response_preview"] = str(data)[:200]
            except:
                print(f"  📦 Response: {response.text[:200]}...")
                test_result["response_preview"] = response.text[:200]
            
            results["passed"] += 1
            test_result["result"] = "PASSED"
        else:
            print(f"  ❌ Status: {response.status_code}")
            print(f"  ⏱️  Response time: {response.elapsed.total_seconds():.3f}s")
            
            try:
                error_data = response.json()
                print(f"  ⚠️  Error: {json.dumps(error_data, indent=2)}")
                test_result["error"] = error_data
            except:
                print(f"  ⚠️  Error: {response.text[:200]}")
                test_result["error"] = response.text[:200]
            
            results["failed"] += 1
            test_result["result"] = "FAILED"
        
        results["tests"].append(test_result)
        return response
        
    except Exception as e:
        print(f"  💥 Exception: {str(e)}")
        results["failed"] += 1
        results["tests"].append({
            "name": name,
            "endpoint": f"{method} {path}",
            "result": "ERROR",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
        return None

def run_all_tests():
    """Run all endpoint tests"""
    
    print_header("INVENTORYSYNC API COMPREHENSIVE TEST SUITE")
    print(f"Base URL: {BASE_URL}")
    print(f"Started at: {results['start_time']}")
    
    # 1. Basic Health Checks
    print_header("1. HEALTH CHECK ENDPOINTS")
    
    test_endpoint("Root Endpoint", "GET", "/")
    test_endpoint("Basic Health", "GET", "/health")
    test_endpoint("API Root", "GET", "/api")
    test_endpoint("Health Status", "GET", "/health/health/")
    test_endpoint("Liveness Probe", "GET", "/health/health/live")
    test_endpoint("Readiness Probe", "GET", "/health/health/ready")
    test_endpoint("System Status", "GET", "/health/health/status")
    test_endpoint("Metrics Summary", "GET", "/health/health/metrics/summary")
    
    # 2. Authentication Endpoints
    print_header("2. AUTHENTICATION ENDPOINTS")
    
    test_endpoint("Auth Status", "GET", "/api/auth/api/v1/auth/status")
    test_endpoint("Install App", "GET", f"/api/auth/api/v1/auth/install?shop={TEST_SHOP}")
    test_endpoint("Dev Setup", "POST", f"/api/auth/api/v1/auth/dev-setup?shop={TEST_SHOP}")
    
    # 3. Monitoring Endpoints
    print_header("3. MONITORING ENDPOINTS")
    
    test_endpoint("Monitoring Health", "GET", "/api/monitoring/api/v1/monitoring/health")
    test_endpoint("Simple Health", "GET", "/api/monitoring/api/v1/monitoring/health/simple")
    test_endpoint("Metrics Summary", "GET", "/api/monitoring/api/v1/monitoring/metrics/summary")
    
    # Admin endpoints (will fail without proper token)
    headers = {"X-Admin-Token": ADMIN_TOKEN}
    test_endpoint("Performance Metrics", "GET", "/api/monitoring/api/v1_monitoring/metrics", headers=headers)
    test_endpoint("Recent Alerts", "GET", "/api/monitoring/api/v1/monitoring/alerts", headers=headers)
    test_endpoint("System Info", "GET", "/api/monitoring/api/v1/monitoring/system", headers=headers)
    test_endpoint("Recent Errors", "GET", "/api/monitoring/api/v1/monitoring/logs/errors", headers=headers)
    test_endpoint("Monitoring Config", "GET", "/api/monitoring/api/v1/monitoring/config", headers=headers)
    
    # 4. API Documentation
    print_header("4. API DOCUMENTATION")
    
    test_endpoint("OpenAPI Schema", "GET", "/openapi.json")
    test_endpoint("Swagger UI", "GET", "/docs")
    test_endpoint("ReDoc", "GET", "/redoc")
    
    # 5. Test Database Connectivity
    print_header("5. DATABASE CONNECTIVITY TEST")
    
    # This will be tested through the health endpoints
    health_response = requests.get(f"{BASE_URL}/health/health/status")
    if health_response.status_code == 200:
        health_data = health_response.json()
        db_status = health_data.get("services", {}).get("database", {})
        redis_status = health_data.get("services", {}).get("redis", {})
        
        print(f"\n📊 Database Status:")
        print(f"  PostgreSQL: {db_status.get('status', 'unknown')} (latency: {db_status.get('latency_ms', 'N/A')}ms)")
        print(f"  Redis: {redis_status.get('status', 'unknown')} (latency: {redis_status.get('latency_ms', 'N/A')}ms)")
    
    # 6. Performance Test
    print_header("6. PERFORMANCE TEST")
    
    print("\nRunning concurrent requests...")
    start_time = time.time()
    
    # Make 10 concurrent requests
    import concurrent.futures
    
    def make_request(i):
        return requests.get(f"{BASE_URL}/health")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request, i) for i in range(10)]
        responses = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"  ⏱️  10 concurrent requests completed in {total_time:.3f}s")
    print(f"  📊 Average response time: {total_time/10:.3f}s per request")
    
    # Summary
    print_header("TEST SUMMARY")
    
    total_tests = results["passed"] + results["failed"]
    duration = (datetime.now() - results["start_time"]).total_seconds()
    
    print(f"\n📊 Test Results:")
    print(f"  Total Tests: {total_tests}")
    print(f"  ✅ Passed: {results['passed']}")
    print(f"  ❌ Failed: {results['failed']}")
    print(f"  ⏱️  Duration: {duration:.2f}s")
    print(f"  🎯 Success Rate: {(results['passed']/total_tests*100):.1f}%")
    
    # Save results to file
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to test_results.json")
    
    return results

def test_shopify_oauth_flow():
    """Test Shopify OAuth flow"""
    print_header("SHOPIFY OAUTH FLOW TEST")
    
    print("\n1. Testing install endpoint...")
    response = requests.get(f"{BASE_URL}/api/auth/api/v1/auth/install", params={"shop": TEST_SHOP})
    
    if response.status_code == 307:  # Redirect
        print("  ✅ Install endpoint returns redirect (expected)")
        print(f"  📍 Redirect URL: {response.headers.get('Location', 'N/A')}")
    else:
        print(f"  ⚠️  Unexpected status: {response.status_code}")
    
    print("\n2. Testing dev setup endpoint...")
    response = requests.post(f"{BASE_URL}/api/auth/api/v1/auth/dev-setup", params={"shop": TEST_SHOP})
    
    if response.status_code == 200:
        data = response.json()
        print("  ✅ Dev setup successful")
        print(f"  📦 Response: {json.dumps(data, indent=2)}")
    else:
        print(f"  ❌ Dev setup failed: {response.status_code}")

def check_marketplace_requirements():
    """Check Shopify marketplace requirements"""
    print_header("SHOPIFY MARKETPLACE REQUIREMENTS CHECK")
    
    requirements = {
        "oauth_flow": False,
        "webhook_support": False,
        "gdpr_compliance": False,
        "billing_api": False,
        "app_bridge": False,
        "security_headers": False,
        "ssl_certificate": False,
        "privacy_policy": False,
        "app_listing": False
    }
    
    print("\n🔍 Checking requirements...")
    
    # 1. OAuth Flow
    try:
        response = requests.get(f"{BASE_URL}/api/auth/api/v1/auth/install", params={"shop": TEST_SHOP})
        requirements["oauth_flow"] = response.status_code in [307, 302]
        print(f"  {'✅' if requirements['oauth_flow'] else '❌'} OAuth Flow")
    except:
        print("  ❌ OAuth Flow")
    
    # 2. Webhook Support
    try:
        response = requests.post(f"{BASE_URL}/api/auth/api/v1/auth/webhook", 
                               headers={"X-Shopify-Topic": "test"})
        requirements["webhook_support"] = response.status_code in [200, 401]
        print(f"  {'✅' if requirements['webhook_support'] else '❌'} Webhook Support")
    except:
        print("  ❌ Webhook Support")
    
    # 3. SSL Certificate
    requirements["ssl_certificate"] = BASE_URL.startswith("https://")
    print(f"  {'✅' if requirements['ssl_certificate'] else '❌'} SSL Certificate")
    
    # 4. Security Headers
    try:
        response = requests.get(BASE_URL)
        headers = response.headers
        has_security_headers = (
            'X-Content-Type-Options' in headers or
            'X-Frame-Options' in headers or
            'Strict-Transport-Security' in headers
        )
        requirements["security_headers"] = has_security_headers
        print(f"  {'✅' if requirements['security_headers'] else '⚠️'} Security Headers")
    except:
        print("  ❌ Security Headers")
    
    # Summary
    passed = sum(1 for v in requirements.values() if v)
    total = len(requirements)
    
    print(f"\n📊 Marketplace Readiness: {passed}/{total} ({passed/total*100:.0f}%)")
    
    print("\n📝 Next Steps for Marketplace Submission:")
    if not requirements["oauth_flow"]:
        print("  • Fix OAuth flow implementation")
    if not requirements["webhook_support"]:
        print("  • Implement webhook endpoints")
    if not requirements["gdpr_compliance"]:
        print("  • Add GDPR compliance endpoints")
    if not requirements["billing_api"]:
        print("  • Implement Shopify Billing API")
    if not requirements["app_bridge"]:
        print("  • Add App Bridge to frontend")
    
    print("\n📋 Required Documentation:")
    print("  • App listing information")
    print("  • Privacy policy URL")
    print("  • Support contact information")
    print("  • App screenshots and demo video")
    print("  • Testing instructions for reviewers")
    
    return requirements

if __name__ == "__main__":
    # Run all tests
    results = run_all_tests()
    
    # Test Shopify OAuth flow
    test_shopify_oauth_flow()
    
    # Check marketplace requirements
    marketplace_ready = check_marketplace_requirements()
    
    # Exit with appropriate code
    sys.exit(0 if results["failed"] == 0 else 1)
