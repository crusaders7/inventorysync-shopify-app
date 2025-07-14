#!/usr/bin/env python3
"""
OAuth Test Tool - Debug Shopify OAuth issues
"""

import os
import sys
import urllib.parse
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings

def test_oauth_setup():
    """Test OAuth configuration"""
    print("🔐 OAuth Configuration Test")
    print("=" * 40)
    
    # Your store details
    domain = 'inventorysync-dev.myshopify.com'
    api_key = settings.shopify_api_key
    api_secret = settings.shopify_api_secret
    
    print(f"Store Domain: {domain}")
    print(f"API Key: {api_key}")
    print(f"API Secret: {'*' * 20}{api_secret[-4:]}")
    print()
    
    # Test different redirect URIs
    redirect_uris = [
        'http://localhost:8000/api/v1/auth/callback',
        'http://localhost:8000/auth/callback',
        'http://localhost:3000/auth/callback',
        'https://localhost:8000/api/v1/auth/callback'
    ]
    
    scopes = 'read_products,write_products,read_inventory,write_inventory,read_locations'
    
    print("🔗 OAuth URLs to Try:")
    print("-" * 25)
    
    for i, redirect_uri in enumerate(redirect_uris, 1):
        oauth_url = (
            f'https://{domain}/admin/oauth/authorize'
            f'?client_id={api_key}'
            f'&scope={scopes}'
            f'&redirect_uri={urllib.parse.quote(redirect_uri)}'
        )
        print(f"{i}. {oauth_url}")
        print(f"   Redirect: {redirect_uri}")
        print()
    
    # Partner Dashboard method
    print("🏪 Partner Dashboard Method:")
    print("-" * 25)
    print("1. Go to: https://partners.shopify.com/4377870/apps/265561079809/overview")
    print("2. Click 'Test on development store'")
    print("3. Select 'inventorysync-dev' store")
    print("4. This should bypass OAuth URL issues")
    print()
    
    # Browser troubleshooting
    print("🌐 Browser Troubleshooting:")
    print("-" * 25)
    print("1. Try in incognito/private window")
    print("2. Disable all browser extensions")
    print("3. Clear cache and cookies for *.shopify.com")
    print("4. Try different browser (Chrome, Firefox, Safari)")
    print("5. Check browser console for JavaScript errors")
    print()
    
    # Manual app installation
    print("🔧 Manual Installation (if OAuth fails):")
    print("-" * 40)
    print("1. Go to your store admin:")
    print(f"   https://{domain}/admin")
    print("2. Go to Apps > Manage private apps")
    print("3. Create a private app with these scopes:")
    print(f"   {scopes}")
    print("4. Use the generated API key/password for testing")
    print()
    
    print("💡 Common Issues:")
    print("-" * 15)
    print("• Ad blockers blocking Shopify analytics")
    print("• Browser security settings too strict")
    print("• Redirect URI mismatch in Partner Dashboard")
    print("• Development store not properly set up")
    print("• Network/firewall blocking localhost")

if __name__ == "__main__":
    test_oauth_setup()