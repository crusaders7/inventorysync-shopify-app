#!/bin/bash

echo "🔗 Connecting to your Shopify Partner App..."
echo "==========================================="
echo ""
echo "App ID: 265561079809"
echo "Store: inventorysync-dev.myshopify.com"
echo ""

# Check if ngrok is installed
if [ -f "frontend/ngrok" ]; then
    echo "✅ ngrok found"
else
    echo "❌ ngrok not found. Please install it first."
    exit 1
fi

echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Get your API credentials from Partner Dashboard:"
echo "   https://partners.shopify.com/4377870/apps/265561079809/api_access"
echo ""
echo "2. Update the .env file with:"
echo "   - SHOPIFY_API_KEY (Client ID)"
echo "   - SHOPIFY_API_SECRET (Client Secret)"
echo ""
echo "3. Start ngrok tunnel:"
echo "   cd frontend && ./ngrok http 8000"
echo ""
echo "4. Update your app URLs in Partner Dashboard with ngrok URL"
echo ""
echo "5. Install the app on your dev store:"
echo "   https://inventorysync-dev.myshopify.com/admin/apps"
echo ""
echo "==========================================="
echo ""
echo "🚀 Quick Install URL Generator:"
echo ""
echo "Once you have your ngrok URL, visit:"
echo "https://inventorysync-dev.myshopify.com/admin/oauth/authorize?"
echo "client_id=YOUR_API_KEY&"
echo "scope=read_products,write_products,read_inventory,write_inventory,read_locations&"
echo "redirect_uri=https://YOUR_NGROK_URL/api/v1/auth/callback"
echo ""