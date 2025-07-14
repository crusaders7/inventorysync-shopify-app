# Deploying InventorySync App Extensions

## Quick Setup Guide

To make custom fields appear directly in Shopify admin product pages, follow these steps:

### 1. Install Shopify CLI (if not already installed)
```bash
npm install -g @shopify/cli @shopify/theme
```

### 2. Deploy the Admin UI Extension
```bash
cd extensions/admin-ui-custom-fields
shopify app generate extension
shopify app deploy
```

### 3. Enable the Extension in Partner Dashboard
1. Go to your [Shopify Partner Dashboard](https://partners.shopify.com)
2. Select your app (InventorySync)
3. Go to **Extensions**
4. Find **Custom Fields Admin**
5. Click **Activate**

### 4. Test in Development Store
1. Install/reinstall the app on `inventorysync-dev.myshopify.com`
2. Go to any product in Shopify admin
3. Look for the **Custom Fields** section or button
4. Click to manage custom fields

## Alternative: App Blocks (Easier)

If the UI extension is complex, use App Blocks instead:

1. **In your theme editor**:
   - Go to **Online Store** → **Themes**
   - Click **Customize**
   - Navigate to a product page
   - Add an **App Block**
   - Select **InventorySync Custom Fields**
   - Save

2. **The block will automatically**:
   - Load custom fields for the current product
   - Show a management interface
   - Save directly to your metafields

## What Merchants Will See

### In Product Admin:
- A new **Custom Fields** section
- **Manage Custom Fields** button
- Badge showing savings vs Shopify Plus
- Direct access to field management

### Features Available:
- ✅ View all custom fields
- ✅ Edit field values
- ✅ Apply templates
- ✅ Bulk operations
- ✅ Import/export data

## Troubleshooting

### Extension Not Showing
1. Clear browser cache
2. Ensure app is installed properly
3. Check app permissions include product write access
4. Verify extension is activated in Partner Dashboard

### Fields Not Loading
1. Check API endpoint: `https://inventorysync.prestigecorp.au/api/metafields/`
2. Verify shop domain is passed correctly
3. Check browser console for errors
4. Ensure CORS is configured properly

### Need Help?
- Email: support@inventorysync.app
- Documentation: `/docs/MERCHANT_GUIDE_CUSTOM_FIELDS.md`
- API Reference: `/backend/api/metafields.py`
