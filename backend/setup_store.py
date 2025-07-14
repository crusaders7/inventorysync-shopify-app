#!/usr/bin/env python3
"""
InventorySync Store Setup CLI
Interactive tool to set up your Shopify store with InventorySync
"""

import os
import sys
import json
import urllib.parse
from datetime import datetime
from typing import Optional
import asyncio

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import AsyncSessionLocal
from models import Store
from config import settings
from sqlalchemy import text
from utils.logging import logger

class StoreSetupCLI:
    def __init__(self):
        self.store_data = {}
        
    def print_header(self):
        """Print welcome header"""
        print("\n" + "="*60)
        print("🛍️  InventorySync Store Setup")
        print("="*60)
        print("This tool will help you connect your Shopify store to InventorySync")
        print("Make sure your backend server is running on http://localhost:8000")
        print("="*60 + "\n")
        
    def get_store_info(self):
        """Get store information from user"""
        print("📋 Store Information")
        print("-" * 20)
        
        # Get store domain
        while True:
            domain = input("Enter your Shopify store domain (e.g., mystore.myshopify.com): ").strip()
            if domain:
                if not domain.endswith('.myshopify.com'):
                    domain += '.myshopify.com'
                self.store_data['domain'] = domain
                break
            print("❌ Please enter a valid domain")
        
        # Get store name
        store_name = input("Enter your store name (optional): ").strip()
        if not store_name:
            store_name = domain.replace('.myshopify.com', '').replace('-', ' ').title()
        self.store_data['name'] = store_name
        
        # Get email
        email = input("Enter your email address: ").strip()
        self.store_data['email'] = email or 'admin@' + domain
        
        print(f"\n✅ Store configured: {self.store_data['name']} ({self.store_data['domain']})")
        
    def show_oauth_instructions(self):
        """Show OAuth setup instructions"""
        print("\n🔐 OAuth Setup")
        print("-" * 20)
        
        # Generate OAuth URL
        api_key = settings.shopify_api_key
        redirect_uri = 'http://localhost:8000/api/v1/auth/callback'
        scopes = 'read_products,write_products,read_inventory,write_inventory,read_locations,read_orders'
        
        oauth_url = (
            f"https://{self.store_data['domain']}/admin/oauth/authorize"
            f"?client_id={api_key}"
            f"&scope={scopes}"
            f"&redirect_uri={urllib.parse.quote(redirect_uri)}"
            f"&state=setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        print("To complete the setup, you need to authorize the app:")
        print("\n1. Copy this URL and paste it in your browser:")
        print(f"   {oauth_url}")
        print("\n2. This will redirect you to Shopify where you can:")
        print("   - Log into your store admin")
        print("   - Review the requested permissions")
        print("   - Click 'Install app' to authorize")
        print("\n3. After authorization, you'll be redirected back to InventorySync")
        print("   (The redirect might show an error page, but that's expected)")
        
        return oauth_url
        
    def create_test_store(self):
        """Create a test store entry in the database"""
        print("\n🏪 Creating Store Entry")
        print("-" * 20)
        
        try:
            # Use synchronous database for setup
            from database import SessionLocal
            db = SessionLocal()
            
            # Check if store already exists
            existing_store = db.execute(
                text("SELECT id FROM stores WHERE shopify_domain = :domain"),
                {'domain': self.store_data['domain']}
            ).fetchone()
            
            if existing_store:
                print(f"⚠️  Store already exists with ID: {existing_store[0]}")
                return existing_store[0]
            
            # Create new store
            db.execute(text("""
                INSERT INTO stores (shopify_domain, access_token, shop_name, email)
                VALUES (:domain, :token, :name, :email)
            """), {
                'domain': self.store_data['domain'],
                'token': 'pending_oauth_setup',
                'name': self.store_data['name'],
                'email': self.store_data['email']
            })
            
            db.commit()
            
            # Get the created store ID
            result = db.execute(
                text("SELECT id FROM stores WHERE shopify_domain = :domain"),
                {'domain': self.store_data['domain']}
            )
            store_id = result.fetchone()[0]
            
            print(f"✅ Store created successfully with ID: {store_id}")
            return store_id
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error creating store: {e}")
            return None
        finally:
            db.close()
            
    def show_next_steps(self, store_id: int, oauth_url: str):
        """Show next steps after setup"""
        print("\n🎯 Next Steps")
        print("-" * 20)
        
        print("1. Complete OAuth authorization:")
        print(f"   Open: {oauth_url}")
        
        print("\n2. Test your API endpoints:")
        print("   Health check: curl http://localhost:8000/health")
        print("   Store info: curl http://localhost:8000/api/v1/dashboard/stores")
        
        print("\n3. Start using InventorySync features:")
        print("   - Custom Fields: Add unlimited fields to products")
        print("   - Workflow Automation: Set up inventory rules")
        print("   - Multi-location: Sync across locations")
        print("   - Forecasting: AI-powered predictions")
        
        print("\n4. Access your store admin:")
        print(f"   https://{self.store_data['domain']}/admin")
        
        print("\n📖 Documentation:")
        print("   Setup Guide: ./SHOPIFY_SETUP.md")
        print("   API Docs: http://localhost:8000/docs")
        
    def run(self):
        """Run the setup process"""
        try:
            self.print_header()
            self.get_store_info()
            
            oauth_url = self.show_oauth_instructions()
            
            proceed = input("\n❓ Create store entry in database? (y/N): ").strip().lower()
            if proceed in ['y', 'yes']:
                store_id = self.create_test_store()
                if store_id:
                    self.show_next_steps(store_id, oauth_url)
                    
                    # Save setup info
                    setup_info = {
                        'store_id': store_id,
                        'domain': self.store_data['domain'],
                        'name': self.store_data['name'],
                        'email': self.store_data['email'],
                        'oauth_url': oauth_url,
                        'setup_date': datetime.now().isoformat()
                    }
                    
                    with open('store_setup.json', 'w') as f:
                        json.dump(setup_info, f, indent=2)
                    
                    print(f"\n💾 Setup info saved to: store_setup.json")
            else:
                print("\n⏭️  Skipping database setup. You can run this again later.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Setup cancelled by user")
        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            logger.error(f"Store setup failed: {e}")

def main():
    """Main entry point"""
    cli = StoreSetupCLI()
    cli.run()

if __name__ == "__main__":
    main()