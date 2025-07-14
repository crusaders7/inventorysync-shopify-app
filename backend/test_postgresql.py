#!/usr/bin/env python3
"""
Test PostgreSQL APIs
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing Health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_custom_fields():
    """Test custom fields endpoint"""
    print("Testing Custom Fields endpoint...")
    response = requests.get(f"{BASE_URL}/api/v1/custom-fields/inventorysync-dev.myshopify.com")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Custom Fields Count: {len(data.get('fields', []))}")
        if data.get('fields'):
            print(f"First Field: {data['fields'][0].get('display_name', 'N/A')}")
    print()

def test_alerts():
    """Test alerts endpoint"""
    print("Testing Alerts endpoint...")
    response = requests.get(f"{BASE_URL}/api/v1/alerts/")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Alerts Count: {data.get('total', 0)}")
    print()

def test_dashboard():
    """Test dashboard stats endpoint"""
    print("Testing Dashboard Stats endpoint...")
    response = requests.get(f"{BASE_URL}/api/v1/dashboard/stats")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total Products: {data.get('total_products', 0)}")
        print(f"Low Stock Count: {data.get('low_stock_count', 0)}")
    print()

def test_industry_templates():
    """Test industry templates endpoint"""
    print("Testing Industry Templates endpoint...")
    response = requests.get(f"{BASE_URL}/api/v1/custom-fields/templates")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, dict) and 'templates' in data:
            templates = data['templates']
            print(f"Industries Count: {len(templates)}")
            first_industry = list(templates.keys())[0] if templates else None
            if first_industry:
                print(f"First Industry: {first_industry}")
                print(f"Fields in {first_industry}: {len(templates[first_industry])}")
    print()

if __name__ == "__main__":
    print("=== Testing PostgreSQL Backend APIs ===\n")
    
    test_health()
    test_custom_fields()
    test_alerts()
    test_dashboard()
    test_industry_templates()
    
    print("=== Test Complete ===")
