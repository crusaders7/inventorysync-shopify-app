#!/usr/bin/env python3
"""
Test Custom Fields Flow
"""

import requests
import json

BASE_URL = "http://localhost:8000"
SHOP_DOMAIN = "inventorysync-dev.myshopify.com"

def test_custom_fields():
    print("=== Testing Custom Fields API ===\n")
    
    # 1. Get existing custom fields
    print("1. Getting existing custom fields...")
    response = requests.get(f"{BASE_URL}/api/v1/custom-fields/{SHOP_DOMAIN}")
    if response.ok:
        data = response.json()
        print(f"✓ Found {data['total']} custom fields")
        for field in data['fields']:
            print(f"  - {field['display_name']} ({field['field_name']}, type: {field['field_type']})")
    else:
        print(f"✗ Failed: {response.status_code} - {response.text}")
    
    # 2. Create a new custom field
    print("\n2. Creating a new custom field...")
    new_field = {
        "field_name": "brand",
        "display_name": "Brand Name",
        "field_type": "text",
        "description": "Product brand",
        "required": True,
        "is_searchable": True,
        "is_filterable": True,
        "category": "product"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/custom-fields/{SHOP_DOMAIN}",
        json=new_field
    )
    
    if response.ok:
        data = response.json()
        print(f"✓ Created field: {data['field_name']} (ID: {data['field_id']})")
    else:
        print(f"✗ Failed: {response.status_code} - {response.text}")
    
    # 3. Get templates
    print("\n3. Getting industry templates...")
    response = requests.get(f"{BASE_URL}/api/v1/custom-fields/templates")
    if response.ok:
        data = response.json()
        print(f"✓ Found {len(data['industries'])} industry templates:")
        for industry in data['industries']:
            print(f"  - {industry}: {len(data['templates'][industry])} fields")
    else:
        print(f"✗ Failed: {response.status_code} - {response.text}")

def test_alerts():
    print("\n\n=== Testing Alerts API ===\n")
    
    # 1. Get alerts
    print("1. Getting alerts...")
    response = requests.get(f"{BASE_URL}/api/v1/alerts/{SHOP_DOMAIN}")
    if response.ok:
        data = response.json()
        print(f"✓ Found {data['total_count']} alerts")
        for alert in data['alerts'][:5]:  # Show first 5
            print(f"  - [{alert['severity'].upper()}] {alert['title']}")
    else:
        print(f"✗ Failed: {response.status_code} - {response.text}")
    
    # 2. Get analytics
    print("\n2. Getting alert analytics...")
    response = requests.get(f"{BASE_URL}/api/v1/alerts/analytics/{SHOP_DOMAIN}")
    if response.ok:
        data = response.json()
        summary = data['summary']
        print(f"✓ Alert Summary (last {data['period_days']} days):")
        print(f"  - Total: {summary['total_alerts']}")
        print(f"  - Active: {summary['active_alerts']}")
        print(f"  - Resolved: {summary['resolved_alerts']}")
        print(f"  - Resolution Rate: {summary['resolution_rate']:.1f}%")
    else:
        print(f"✗ Failed: {response.status_code} - {response.text}")
    
    # 3. Create a test alert
    print("\n3. Creating a test alert...")
    new_alert = {
        "alert_type": "manual",
        "severity": "high",
        "title": "Test Alert - Custom Fields Working!",
        "message": "This is a test alert to verify the system is working correctly.",
        "recommended_action": "No action needed - this is just a test",
        "notification_channels": ["email"]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/alerts/{SHOP_DOMAIN}",
        json=new_alert
    )
    
    if response.ok:
        data = response.json()
        print(f"✓ Created alert: {data['title']} (ID: {data['id']})")
    else:
        print(f"✗ Failed: {response.status_code} - {response.text}")

def test_workflows():
    print("\n\n=== Testing Workflows API ===\n")
    
    # Get workflow templates
    print("1. Getting workflow templates...")
    response = requests.get(f"{BASE_URL}/api/v1/workflows/templates")
    if response.ok:
        data = response.json()
        print(f"✓ Found workflow templates")
        print(f"  Templates available: {json.dumps(data, indent=2)}")
    else:
        print(f"✗ Failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    print("🚀 Testing InventorySync APIs...\n")
    
    test_custom_fields()
    test_alerts()
    test_workflows()
    
    print("\n\n✅ All tests completed!")
    print("\nYou can now:")
    print("1. Open http://localhost:3000 in your browser")
    print("2. Navigate to Custom Fields to see your fields")
    print("3. Check Alerts to see the test alert")
    print("4. Try Industry Templates to apply pre-built configurations")
