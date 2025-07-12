# Shopify Partners Setup Guide

## Quick Start

### 1. Create Shopify Partners Account
- Go to: https://partners.shopify.com/signup
- Sign up with your business details

### 2. Create Your App
1. Login to Partners Dashboard
2. Click **"Apps"** → **"Create app"**
3. Choose **"Create app manually"**

### 3. App Configuration
Fill in these exact values:

**App name:** InventorySync

**App URL:** 
```
http://localhost:8000
```

**Allowed redirection URL(s):** (Add ALL of these)
```
http://localhost:8000/api/v1/auth/callback
http://localhost:3000/auth/callback
http://localhost:3000/auth/shopify/callback
https://localhost:3000/auth/callback
https://localhost:3000/auth/shopify/callback
```

### 4. Get Your Credentials
After creating the app:
1. Go to **"Client credentials"** section
2. Copy your **Client ID** (should be: `b9e83419bf510cff0b85cf446b4a7750`)
3. Copy your **Client secret** (this is what you need!)

### 5. Update Your Local App
Run this command:
```bash
cd /home/brend/inventorysync-shopify-app
python scripts/update_shopify_credentials.py
```

Enter your Client secret when prompted.

### 6. Configure Webhooks (Later)
In the Partners dashboard:
1. Go to **"Webhooks"** section
2. Set webhook URL: `https://your-ngrok-url.ngrok.io/api/v1/webhooks`
3. Subscribe to these topics:
   - products/create
   - products/update
   - products/delete
   - inventory_levels/update
   - app/uninstalled

### 7. Install on Development Store
1. From your app page, click **"Select store"**
2. Choose your development store
3. Click **"Install app"**

## Troubleshooting

### Can't find Client credentials?
- Look for **"API credentials"** or **"Client credentials"** tab
- Sometimes it's under **"App setup"** → **"API access"**

### Getting 401 Unauthorized?
- Make sure you copied the entire Client secret
- Check there are no extra spaces
- Restart your backend server after updating .env

### OAuth redirect not working?
- Ensure all redirect URLs are added exactly as shown
- Check your backend is running on port 8000
- Check your frontend is running on port 3000

## Development Store

If you don't have a development store:
1. In Partners dashboard, go to **"Stores"**
2. Click **"Add store"**
3. Choose **"Development store"**
4. Fill in store details
5. Your store URL will be: `your-store-name.myshopify.com`
