#!/usr/bin/env python3
"""
Configure Shopify webhooks via API
"""

import requests
import json
import sqlite3
import sys
from typing import List, Dict

def get_store_access_token(shop_domain: str) -> str:
    """Get access token for store"""
    conn = sqlite3.connect('inventorysync_dev.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT access_token FROM stores WHERE shopify_domain = ?", (shop_domain,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def create_webhook(shop_domain: str, access_token: str, webhook_data: Dict) -> bool:
    """Create a webhook in Shopify"""
    url = f"https://{shop_domain}/admin/api/2023-10/webhooks.json"
    
    headers = {
        'X-Shopify-Access-Token': access_token,
        'Content-Type': 'application/json'
    }
    
    payload = {
        "webhook": webhook_data
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        created_webhook = response.json()
        webhook_id = created_webhook['webhook']['id']
        topic = created_webhook['webhook']['topic']
        
        print(f"✅ Created webhook: {topic} (ID: {webhook_id})")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating webhook {webhook_data['topic']}: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return False

def list_existing_webhooks(shop_domain: str, access_token: str) -> List[Dict]:
    """List existing webhooks"""
    url = f"https://{shop_domain}/admin/api/2023-10/webhooks.json"
    
    headers = {
        'X-Shopify-Access-Token': access_token,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        webhooks = data.get('webhooks', [])
        
        print(f"📋 Found {len(webhooks)} existing webhooks:")
        for webhook in webhooks:
            print(f"  - {webhook['topic']}: {webhook['address']} (ID: {webhook['id']})")
        
        return webhooks
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error listing webhooks: {e}")
        return []

def delete_webhook(shop_domain: str, access_token: str, webhook_id: int) -> bool:
    """Delete a webhook"""
    url = f"https://{shop_domain}/admin/api/2023-10/webhooks/{webhook_id}.json"
    
    headers = {
        'X-Shopify-Access-Token': access_token,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        
        print(f"✅ Deleted webhook ID: {webhook_id}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error deleting webhook {webhook_id}: {e}")
        return False

def configure_webhooks():
    """Configure all webhooks for the store"""
    shop_domain = "inventorysync-dev.myshopify.com"
    ngrok_url = "https://9c15ccc07c42.ngrok-free.app"
    
    # Get access token
    access_token = get_store_access_token(shop_domain)
    if not access_token:
        print(f"❌ No access token found for store: {shop_domain}")
        return False
    
    print(f"🔧 Configuring webhooks for: {shop_domain}")
    print(f"📡 Using ngrok URL: {ngrok_url}")
    
    # List existing webhooks
    print("\n📋 Checking existing webhooks...")
    existing_webhooks = list_existing_webhooks(shop_domain, access_token)
    
    # Clean up old webhooks (skip for automation)
    print(f"📝 Skipping cleanup - will create new webhooks")
    
    # Define webhooks to create
    webhooks_to_create = [
        {
            "topic": "products/create",
            "address": f"{ngrok_url}/api/v1/webhooks/products/create",
            "format": "json"
        },
        {
            "topic": "products/update", 
            "address": f"{ngrok_url}/api/v1/webhooks/products/update",
            "format": "json"
        },
        {
            "topic": "products/delete",
            "address": f"{ngrok_url}/api/v1/webhooks/products/delete", 
            "format": "json"
        },
        {
            "topic": "orders/create",
            "address": f"{ngrok_url}/api/v1/webhooks/orders/create",
            "format": "json"
        }
    ]
    
    # Create webhooks
    print(f"\n🔄 Creating {len(webhooks_to_create)} webhooks...")
    created_count = 0
    
    for webhook_data in webhooks_to_create:
        if create_webhook(shop_domain, access_token, webhook_data):
            created_count += 1
    
    print(f"\n✅ Successfully created {created_count}/{len(webhooks_to_create)} webhooks!")
    
    # List final webhooks
    print("\n📋 Final webhook configuration:")
    list_existing_webhooks(shop_domain, access_token)
    
    if created_count > 0:
        print(f"\n🎉 Webhooks are now configured!")
        print(f"📱 Test by creating/updating products in: https://admin.shopify.com/store/inventorysync-dev")
        print(f"🔍 Monitor webhook activity at: http://127.0.0.1:4040")
        print(f"📊 Watch backend logs for real-time updates")
    
    return created_count > 0

def main():
    """Main function"""
    print("🚀 Shopify Webhook Configuration Tool")
    print("=" * 50)
    
    success = configure_webhooks()
    
    if success:
        print("\n✅ Webhook configuration completed successfully!")
        return 0
    else:
        print("\n❌ Webhook configuration failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())