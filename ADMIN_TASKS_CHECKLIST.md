# 📋 Admin Tasks Checklist

## 1. Partners Dashboard Configuration ✏️

### Go to: https://partners.shopify.com/4377870/apps/265561079809/edit

Update these fields:

### App URL
```
https://inventorysync-shopify-app-production.up.railway.app
```

### Allowed redirection URL(s)
Add ALL of these (one per line):
```
https://inventorysync-shopify-app-production.up.railway.app/api/v1/auth/callback
https://inventorysync-shopify-app-production.up.railway.app/api/auth/callback
https://inventorysync-shopify-app-production.up.railway.app/auth/callback
https://inventorysync-shopify-app-production.up.railway.app/auth/shopify/callback
http://localhost:8000/api/v1/auth/callback
http://localhost:3000/auth/callback
```

### Get Your API Secret
- [ ] Copy the API secret key from Partners Dashboard
- [ ] Note it down securely (you'll need it for Railway)

## 2. Railway Environment Variables 🚂

### Go to your Railway project dashboard

1. Click on your service
2. Go to "Variables" tab
3. Click "RAW Editor"
4. Copy and paste from RAILWAY_ENV_VARS.txt
5. Replace `YOUR_API_SECRET_FROM_PARTNERS_DASHBOARD` with actual secret
6. Click "Save"

## 3. Create Development Store 🏪

In Partners Dashboard:

1. Go to "Stores" → "Add store"
2. Choose "Development store"
3. Store name: `inventorysync-test`
4. Store type: Development
5. Click "Create store"

## 4. Test Installation Flow 🧪

1. Get your test store URL: `inventorysync-test.myshopify.com`
2. Open this URL in your browser:
   ```
   https://inventorysync-shopify-app-production.up.railway.app/api/v1/auth/install?shop=inventorysync-test.myshopify.com
   ```
3. You should be redirected to Shopify's OAuth page
4. Click "Install app"
5. Should redirect back to your app

## 5. Quick API Tests 🔍

Test these endpoints to ensure everything works:

```bash
# Health check (should return 200)
curl https://inventorysync-shopify-app-production.up.railway.app/health

# API info (should return endpoint list)
curl https://inventorysync-shopify-app-production.up.railway.app/api
```

## 6. Prepare App Listing Info 📝

### Basic Information
- **App name**: InventorySync Pro
- **App handle**: inventorysync-pro
- **Summary** (70 chars): Advanced inventory management with custom fields & multi-location support

### Detailed Description
```
InventorySync Pro transforms how you manage inventory across your Shopify store. Built for growing businesses that need more than basic stock tracking.

KEY FEATURES:
• Unlimited Custom Fields - Track any product attribute (materials, dimensions, compliance data)
• Multi-Location Management - AI-powered transfer suggestions optimize stock across locations
• Smart Alerts - Never run out of stock with predictive notifications
• Bulk Operations - Update hundreds of products in seconds
• Real-Time Sync - Always accurate inventory levels
• Advanced Analytics - Gain insights into stock performance

PERFECT FOR:
• Multi-location retailers
• Businesses with complex inventory needs
• Stores tracking custom product attributes
• Growing brands ready to scale

PRICING:
Starter ($29/mo) - Up to 1,000 products
Growth ($49/mo) - Up to 10,000 products
Enterprise ($99/mo) - Unlimited products + API access

14-day free trial. No credit card required.
```

### Search Terms
```
inventory, stock, custom fields, multi location, warehouse, inventory sync, stock management, inventory tracking, product fields, bulk update
```

## 7. Webhook Configuration Check ✓

Verify these webhooks are listed in Partners Dashboard under "Webhooks":

- [ ] products/create
- [ ] products/update
- [ ] products/delete
- [ ] inventory_levels/update
- [ ] app/uninstalled
- [ ] customers/data_request (GDPR)
- [ ] customers/redact (GDPR)
- [ ] shop/redact (GDPR)

## 8. Final Pre-Submission Checklist ✅

- [ ] Railway environment variables set
- [ ] Partners Dashboard URLs updated
- [ ] API secret configured in Railway
- [ ] Test installation successful
- [ ] Health endpoint returns 200
- [ ] OAuth flow completes
- [ ] Webhooks registered
- [ ] GDPR endpoints tested

## 🎯 Next: Marketing Assets

Once admin tasks are complete, you'll need:
1. App icon (1024x1024px)
2. App banner (1920x1080px)
3. Screenshots (1280x800px, min 3)

## 📞 Need Help?

- Shopify Partners Slack: partners.shopify.com/slack
- Developer Docs: shopify.dev/apps
- Support: partners@shopify.com
