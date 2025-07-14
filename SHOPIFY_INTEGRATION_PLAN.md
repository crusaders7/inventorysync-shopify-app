# Shopify Admin Integration Plan for InventorySync Custom Fields

## Overview
We'll implement custom fields that appear directly in the Shopify admin product pages using App Blocks and metafields.

## Approach Options

### Option 1: Metafields API (Recommended) ✅
- Use Shopify's native metafields to store custom field data
- Create a custom app section in the product admin page
- Leverage Shopify's built-in metafield editor UI
- No need for complex UI extensions

### Option 2: App Embed Blocks
- Create app blocks that merchants can add to their product pages
- More flexible but requires theme customization

### Option 3: Admin UI Extensions (Complex)
- Direct integration into admin pages
- Requires newer Shopify CLI and complex setup

## Implementation Steps (Option 1 - Metafields)

### 1. Backend API Updates
```python
# Create metafield definitions for the shop
POST /api/v1/metafields/definitions
{
  "namespace": "inventorysync",
  "key": "custom_fields",
  "type": "json",
  "name": "Custom Product Fields",
  "description": "Additional product information"
}
```

### 2. Frontend Integration
- Update the app to use Shopify App Bridge
- Create a seamless experience within the admin
- Use Polaris components for consistency

### 3. Core Features to Implement
1. **Custom Field Management**
   - Create/edit field definitions
   - Field types: text, number, date, select, multi-select
   - Validation rules

2. **Product Integration**
   - Read/write custom fields on products
   - Bulk editing capabilities
   - Import/export functionality

3. **Templates**
   - Industry-specific field templates
   - Quick setup for common use cases

## Simplified Architecture

```
┌─────────────────────┐
│  Shopify Admin      │
│  Product Page       │
└──────────┬──────────┘
           │
           │ iframe embed
           │
┌──────────▼──────────┐
│  InventorySync App  │
│  (Custom Fields UI) │
└──────────┬──────────┘
           │
           │ API calls
           │
┌──────────▼──────────┐
│  Backend API        │
│  - Metafields CRUD  │
│  - Templates        │
│  - Bulk Operations  │
└─────────────────────┘
```

## Quick Start Implementation

### Step 1: Update Backend for Metafields
- Add endpoints to manage Shopify metafields
- Store field definitions in our database
- Sync with Shopify's metafield API

### Step 2: Create Embedded App UI
- Single page that loads in Shopify admin
- Shows custom fields for current product
- Allows editing and saving

### Step 3: Deploy and Test
- Deploy to Railway
- Test in inventorysync-dev.myshopify.com
- Ensure seamless integration

## Benefits of This Approach
- ✅ No complex UI extensions needed
- ✅ Works with current Shopify admin
- ✅ Uses native Shopify features (metafields)
- ✅ Can be implemented quickly
- ✅ Merchants see custom fields directly in product pages

## Next Actions
1. Implement metafield API endpoints
2. Create embedded app UI for custom fields
3. Test integration with development store
4. Deploy to production
