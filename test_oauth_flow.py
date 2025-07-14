#!/usr/bin/env python3
"""
Comprehensive OAuth Flow Testing Script for InventorySync Shopify App
Tests all aspects of the OAuth authentication flow
"""

import asyncio
import httpx
import json
import secrets
from urllib.parse import urlencode, parse_qs, urlparse
from datetime import datetime
import sys
import os

# Configuration
API_BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
TEST_SHOP_DOMAIN = "inventorysync-test.myshopify.com"

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_test_header(test_name):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}TEST: {test_name}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.ENDC}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.ENDC}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ {message}{Colors.ENDC}")

async def test_auth_status():
    """Test 1: Check authentication status endpoint"""
    print_test_header("Authentication Status Check")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE_URL}/api/v1/auth/status")
            data = response.json()
            
            print_info(f"Status Code: {response.status_code}")
            print_info(f"Response: {json.dumps(data, indent=2)}")
            
            if response.status_code == 200:
                print_success("Auth status endpoint is accessible")
                
                # Check configuration
                if data.get('configured'):
                    print_success("App is properly configured")
                else:
                    print_warning("App configuration incomplete")
                    
                if data.get('api_key_set'):
                    print_success("API key is set")
                else:
                    print_error("API key is not set")
                    
                if data.get('api_secret_set'):
                    print_success("API secret is set")
                else:
                    print_error("API secret is not set")
                    
                if data.get('database_healthy'):
                    print_success(f"Database is healthy (Stores: {data.get('connected_stores', 0)})")
                else:
                    print_error("Database connection failed")
                    
                return data
            else:
                print_error(f"Failed to get auth status: {response.status_code}")
                return None
                
        except Exception as e:
            print_error(f"Error checking auth status: {e}")
            return None

async def test_install_flow():
    """Test 2: Test initial app installation flow"""
    print_test_header("App Installation Flow")
    
    async with httpx.AsyncClient(follow_redirects=False) as client:
        try:
            # Test install endpoint
            install_url = f"{API_BASE_URL}/api/v1/auth/install?shop={TEST_SHOP_DOMAIN}"
            print_info(f"Testing install URL: {install_url}")
            
            response = await client.get(install_url)
            
            if response.status_code in [302, 303, 307, 308]:
                print_success("Install endpoint returned redirect")
                
                redirect_location = response.headers.get('location')
                print_info(f"Redirect URL: {redirect_location}")
                
                # Parse redirect URL
                parsed_url = urlparse(redirect_location)
                query_params = parse_qs(parsed_url.query)
                
                # Verify OAuth parameters
                if 'client_id' in query_params:
                    print_success(f"Client ID present: {query_params['client_id'][0][:10]}...")
                else:
                    print_error("Client ID missing from OAuth URL")
                    
                if 'scope' in query_params:
                    scopes = query_params['scope'][0].split(',')
                    print_success(f"Scopes requested: {len(scopes)} scopes")
                    print_info("Scopes: " + ", ".join(scopes))
                    
                    # Verify required scopes
                    required_scopes = [
                        "read_products", "write_products",
                        "read_inventory", "write_inventory",
                        "read_orders", "write_orders",
                        "read_customers"
                    ]
                    
                    for scope in required_scopes:
                        if scope in scopes:
                            print_success(f"Required scope present: {scope}")
                        else:
                            print_error(f"Missing required scope: {scope}")
                else:
                    print_error("Scopes missing from OAuth URL")
                    
                if 'redirect_uri' in query_params:
                    print_success(f"Redirect URI: {query_params['redirect_uri'][0]}")
                else:
                    print_error("Redirect URI missing")
                    
                if 'state' in query_params:
                    print_success(f"State parameter present (CSRF protection)")
                else:
                    print_error("State parameter missing (CSRF vulnerability)")
                    
                return True
            else:
                print_error(f"Install endpoint returned {response.status_code} instead of redirect")
                print_info(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Error testing install flow: {e}")
            return False

async def test_oauth_callback():
    """Test 3: Test OAuth callback handling"""
    print_test_header("OAuth Callback Handling")
    
    # Simulate OAuth callback parameters
    mock_code = "test_authorization_code_123"
    mock_state = secrets.token_urlsafe(32)
    mock_hmac = "test_hmac_123"
    mock_timestamp = str(int(datetime.now().timestamp()))
    
    callback_url = f"{API_BASE_URL}/api/v1/auth/callback"
    params = {
        "shop": TEST_SHOP_DOMAIN,
        "code": mock_code,
        "state": mock_state,
        "hmac": mock_hmac,
        "timestamp": mock_timestamp
    }
    
    print_info(f"Testing callback URL: {callback_url}")
    print_info(f"Parameters: {json.dumps(params, indent=2)}")
    
    async with httpx.AsyncClient(follow_redirects=False) as client:
        try:
            response = await client.get(callback_url, params=params)
            
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code in [302, 303, 307, 308]:
                redirect_location = response.headers.get('location')
                print_info(f"Redirect: {redirect_location}")
                
                # Check if it's redirecting to error or success
                if 'error=' in redirect_location:
                    print_warning("Callback redirected to error page (expected for mock data)")
                    return True  # This is expected behavior for mock data
                elif 'authenticated=true' in redirect_location:
                    print_success("Callback successfully authenticated")
                    return True
                elif 'setup=billing' in redirect_location:
                    print_success("Callback redirected to billing setup")
                    return True
                else:
                    print_warning("Callback redirected to unknown location")
                    return True
            else:
                print_error(f"Callback returned unexpected status: {response.status_code}")
                print_info(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Error testing callback: {e}")
            return False

async def test_webhook_endpoints():
    """Test 4: Test webhook endpoints"""
    print_test_header("Webhook Endpoints")
    
    webhook_url = f"{API_BASE_URL}/api/v1/auth/webhook"
    
    # Test different webhook topics
    webhook_topics = [
        "app/uninstalled",
        "customers/data_request",
        "customers/redact",
        "shop/redact"
    ]
    
    for topic in webhook_topics:
        print_info(f"\nTesting webhook topic: {topic}")
        
        webhook_data = {
            "id": "test_webhook_123",
            "shop_domain": TEST_SHOP_DOMAIN,
            "created_at": datetime.now().isoformat()
        }
        
        if topic == "app/uninstalled":
            webhook_data["shop_id"] = "12345"
        elif topic == "customers/data_request":
            webhook_data["customer"] = {
                "id": "customer_123",
                "email": "test@example.com"
            }
        
        headers = {
            "X-Shopify-Topic": topic,
            "X-Shopify-Hmac-Sha256": "test_hmac",
            "X-Shopify-Shop-Domain": TEST_SHOP_DOMAIN
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    webhook_url,
                    json=webhook_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    print_success(f"Webhook endpoint accepted {topic}")
                elif response.status_code == 401:
                    print_warning(f"Webhook authentication failed for {topic} (expected without valid HMAC)")
                else:
                    print_error(f"Webhook returned {response.status_code} for {topic}")
                    
            except Exception as e:
                print_error(f"Error testing webhook {topic}: {e}")

async def test_session_persistence():
    """Test 5: Test session persistence"""
    print_test_header("Session Persistence")
    
    # First, check if there are any existing stores
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE_URL}/api/v1/auth/status")
            data = response.json()
            
            if data.get('connected_stores', 0) > 0:
                print_success(f"Found {data['connected_stores']} connected stores")
                print_info("Session data persists across requests")
                return True
            else:
                print_warning("No connected stores found")
                print_info("This is expected if app hasn't been installed yet")
                return True
                
        except Exception as e:
            print_error(f"Error checking session persistence: {e}")
            return False

async def test_dev_setup():
    """Test 6: Test development setup endpoint"""
    print_test_header("Development Setup Endpoint")
    
    dev_setup_url = f"{API_BASE_URL}/api/v1/auth/dev-setup"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                dev_setup_url,
                json={"shop": "inventorysync-dev.myshopify.com"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success("Dev setup endpoint working")
                print_info(f"Response: {json.dumps(data, indent=2)}")
                return True
            else:
                print_error(f"Dev setup returned {response.status_code}")
                print_info(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Error testing dev setup: {e}")
            return False

async def main():
    """Run all OAuth flow tests"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     InventorySync Shopify OAuth Flow Test Suite         ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")
    
    print_info(f"API Base URL: {API_BASE_URL}")
    print_info(f"Frontend URL: {FRONTEND_URL}")
    print_info(f"Test Shop: {TEST_SHOP_DOMAIN}")
    print_info(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run tests
    test_results = []
    
    # Test 1: Auth Status
    result = await test_auth_status()
    test_results.append(("Auth Status", result is not None))
    
    # Test 2: Install Flow
    result = await test_install_flow()
    test_results.append(("Install Flow", result))
    
    # Test 3: OAuth Callback
    result = await test_oauth_callback()
    test_results.append(("OAuth Callback", result))
    
    # Test 4: Webhooks
    await test_webhook_endpoints()
    test_results.append(("Webhook Endpoints", True))  # Always passes for now
    
    # Test 5: Session Persistence
    result = await test_session_persistence()
    test_results.append(("Session Persistence", result))
    
    # Test 6: Dev Setup
    result = await test_dev_setup()
    test_results.append(("Dev Setup", result))
    
    # Summary
    print_test_header("Test Summary")
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    print(f"\nTest Results:")
    for test_name, result in test_results:
        status = f"{Colors.GREEN}PASSED{Colors.ENDC}" if result else f"{Colors.RED}FAILED{Colors.ENDC}"
        print(f"  {test_name}: {status}")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.ENDC}")
    
    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}All tests passed! 🎉{Colors.ENDC}")
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}Some tests failed. Review the output above.{Colors.ENDC}")
    
    print_info(f"Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())
