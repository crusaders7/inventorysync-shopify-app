#!/usr/bin/env python3
"""
Quick OAuth Test Script for InventorySync
Tests the OAuth flow with your development store
"""

import os
import sys
from urllib.parse import urlencode
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_install_url(shop_domain, ngrok_url=None):
    """Generate the OAuth install URL for testing"""
    
    api_key = os.getenv('SHOPIFY_API_KEY', 'YOUR_API_KEY')
    scopes = os.getenv('SHOPIFY_SCOPES', 'read_products,write_products,read_inventory,write_inventory,read_locations')
    
    if ngrok_url:
        redirect_uri = f"{ngrok_url}/api/v1/auth/callback"
    else:
        redirect_uri = "http://localhost:8000/api/v1/auth/callback"
    
    params = {
        'client_id': api_key,
        'scope': scopes,
        'redirect_uri': redirect_uri,
        'state': 'test123',
        'grant_options[]': 'per-user'
    }
    
    shop_name = shop_domain.replace('.myshopify.com', '')
    install_url = f"https://{shop_name}.myshopify.com/admin/oauth/authorize?{urlencode(params)}"
    
    return install_url

def main():
    print("🧪 InventorySync OAuth Test")
    print("==========================\n")
    
    # Your development store
    shop_domain = "inventorysync-dev.myshopify.com"
    
    print(f"Testing with store: {shop_domain}")
    print(f"API Key: {os.getenv('SHOPIFY_API_KEY', 'NOT SET - Please update .env')}\n")
    
    # Generate URLs
    print("📋 Install URLs:\n")
    
    print("1. For localhost testing:")
    print(generate_install_url(shop_domain))
    print("\n2. For ngrok testing (replace YOUR_NGROK_URL):")
    print(generate_install_url(shop_domain, "https://YOUR_NGROK_URL"))
    
    print("\n✅ Steps to test:")
    print("1. Make sure backend is running: python main.py")
    print("2. Visit the install URL in your browser")
    print("3. Approve the app permissions")
    print("4. Check backend logs for OAuth callback")
    
    print("\n🔍 Check your Partner Dashboard for API credentials:")
    print("https://partners.shopify.com/4377870/apps/265561079809/api_access")

if __name__ == "__main__":
    main()