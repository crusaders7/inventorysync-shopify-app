#!/usr/bin/env python3
"""
Script to update Shopify credentials in the .env file
"""

import os
import sys

def update_env_file():
    backend_env_path = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
    
    print("🔐 Shopify Credentials Updater")
    print("================================")
    print("\nThis script will help you update your Shopify API credentials.")
    print("\nYou need to get these from: https://partners.shopify.com")
    print("Go to Apps -> Your App -> Client credentials\n")
    
    # Get API Secret
    api_secret = input("Enter your Shopify API Secret (Client secret): ").strip()
    
    if not api_secret:
        print("❌ API Secret cannot be empty!")
        return
    
    # Get Webhook Secret (optional for now)
    webhook_secret = input("\nEnter your Webhook Secret (press Enter to skip for now): ").strip()
    
    # Read current .env file
    try:
        with open(backend_env_path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"❌ .env file not found at {backend_env_path}")
        return
    
    # Update the lines
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('SHOPIFY_API_SECRET='):
            lines[i] = f'SHOPIFY_API_SECRET={api_secret}\n'
            updated = True
            print(f"✅ Updated API Secret")
        elif line.startswith('SHOPIFY_WEBHOOK_SECRET=') and webhook_secret:
            lines[i] = f'SHOPIFY_WEBHOOK_SECRET={webhook_secret}\n'
            print(f"✅ Updated Webhook Secret")
    
    if not updated:
        print("❌ Could not find SHOPIFY_API_SECRET in .env file")
        return
    
    # Write back to file
    with open(backend_env_path, 'w') as f:
        f.writelines(lines)
    
    print("\n✅ Successfully updated .env file!")
    print("\n📋 Next steps:")
    print("1. Install your app on your development store")
    print("2. Start the backend server: cd backend && source venv/bin/activate && python -m uvicorn main:app --reload")
    print("3. Start the frontend: cd frontend && npm run dev")
    print("4. Visit http://localhost:3000 to use your app")

if __name__ == "__main__":
    update_env_file()
