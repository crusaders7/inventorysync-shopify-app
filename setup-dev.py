#!/usr/bin/env python3
"""
Quick setup script for InventorySync development
"""
import os
import sys
import sqlite3
import subprocess
import time
import requests
from datetime import datetime

def setup_database():
    """Create and setup the SQLite database with a dev store"""
    print("Setting up database...")
    
    # Create database connection
    db_path = os.path.join(os.path.dirname(__file__), 'backend', 'inventorysync_dev.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # The stores table already exists from SQLAlchemy
    # Check if dev store already exists
    cursor.execute("SELECT * FROM stores WHERE shopify_domain = ?", ('inventorysync-dev.myshopify.com',))
    existing = cursor.fetchone()
    
    if not existing:
        # Insert dev store
        cursor.execute('''
            INSERT INTO stores (
                shopify_domain, 
                shop_name, 
                email,
                access_token,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            'inventorysync-dev.myshopify.com',
            'InventorySync Dev Store',
            'dev@inventorysync.com',
            'shpat_dev_token_123456789',  # Mock access token
            datetime.now(),
            datetime.now()
        ))
        print("✅ Dev store created in database")
    else:
        print("✅ Dev store already exists in database")
    
    # Create other necessary tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id INTEGER NOT NULL,
            shopify_location_id TEXT NOT NULL,
            name TEXT NOT NULL,
            address1 TEXT,
            address2 TEXT,
            city TEXT,
            province TEXT,
            country TEXT,
            zip TEXT,
            phone TEXT,
            is_active BOOLEAN DEFAULT 1,
            is_primary BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (store_id) REFERENCES stores(id),
            UNIQUE(store_id, shopify_location_id)
        )
    ''')
    
    # Add a default location for the dev store
    cursor.execute("SELECT id FROM stores WHERE shopify_domain = ?", ('inventorysync-dev.myshopify.com',))
    result = cursor.fetchone()
    if result:
        store_id = result[0]
    else:
        print("Error: Could not find store")
        return
    
    cursor.execute("SELECT * FROM locations WHERE store_id = ?", (store_id,))
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO locations (
                store_id,
                shopify_location_id,
                name,
                is_active,
                is_primary
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            store_id,
            'location_dev_123',
            'Main Warehouse',
            1,
            1
        ))
        print("✅ Dev location created in database")
    
    conn.commit()
    conn.close()
    print("✅ Database setup complete")

def update_frontend_env():
    """Update frontend to use correct API URL"""
    env_path = os.path.join(os.path.dirname(__file__), 'frontend', '.env')
    with open(env_path, 'w') as f:
        f.write("VITE_API_URL=http://localhost:8000\n")
        f.write("VITE_SHOPIFY_API_KEY=b9e83419bf510cff0b85cf446b4a7750\n")
    print("✅ Frontend .env file created")

def set_auth_cookie():
    """Set authentication in localStorage via a simple HTML file"""
    html_content = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Setting up InventorySync...</title>
    </head>
    <body>
        <h2>Setting up InventorySync Dev Environment...</h2>
        <script>
            localStorage.setItem('shopify_authenticated', 'true');
            localStorage.setItem('shopify_shop_domain', 'inventorysync-dev.myshopify.com');
            localStorage.setItem('shopify_access_token', 'shpat_dev_token_123456789');
            setTimeout(() => {
                window.location.href = 'http://localhost:3000/?authenticated=true&shop=inventorysync-dev.myshopify.com';
            }, 1000);
        </script>
    </body>
    </html>
    '''
    
    setup_path = os.path.join(os.path.dirname(__file__), 'frontend', 'public', 'setup-dev.html')
    os.makedirs(os.path.dirname(setup_path), exist_ok=True)
    with open(setup_path, 'w') as f:
        f.write(html_content)
    print("✅ Auth setup file created")
    print("\n📌 TO COMPLETE SETUP:")
    print("1. Make sure both servers are running")
    print("2. Open http://localhost:3000/setup-dev.html in your browser")
    print("3. This will set up authentication and redirect you to the app")

def main():
    print("🚀 InventorySync Dev Setup")
    print("=" * 40)
    
    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    os.chdir(backend_dir)
    
    # Setup database
    setup_database()
    
    # Update frontend env
    update_frontend_env()
    
    # Create auth setup file
    set_auth_cookie()
    
    print("\n✅ Setup complete!")
    print("\n📝 Next steps:")
    print("1. Start the backend server:")
    print("   cd backend && source venv/bin/activate && python main.py")
    print("\n2. Start the frontend server (in a new terminal):")
    print("   cd frontend && npm run dev")
    print("\n3. Open http://localhost:3000/setup-dev.html to complete authentication")
    
if __name__ == "__main__":
    main()
