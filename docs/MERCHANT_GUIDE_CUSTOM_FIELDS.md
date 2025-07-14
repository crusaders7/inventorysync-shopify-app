# InventorySync Custom Fields Guide

## Save $1,971/month vs Shopify Plus! 💰

Welcome to InventorySync's Custom Fields feature - the smart way to add unlimited custom fields to your products without paying for Shopify Plus.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Why InventorySync Custom Fields?](#why-inventorysync-custom-fields)
3. [Getting Started](#getting-started)
4. [Industry Templates](#industry-templates)
5. [Managing Custom Fields](#managing-custom-fields)
6. [Field Types](#field-types)
7. [Bulk Operations](#bulk-operations)
8. [Import/Export](#importexport)
9. [FAQ](#faq)
10. [Support](#support)

## Quick Start

1. **Install InventorySync** from the Shopify App Store
2. **Navigate to any product** in your Shopify admin
3. **Click "Manage Custom Fields"** in the InventorySync section
4. **Apply an industry template** or create your own fields
5. **Start saving data!**

## Why InventorySync Custom Fields?

### The Problem
- Shopify Basic/Standard plans have limited metafield capabilities
- Shopify Plus costs $2,000+/month just for advanced features
- Many merchants need custom fields but can't justify the Plus price

### Our Solution
- **Full custom field functionality** for just $29-149/month
- **Save $1,971/month** compared to Shopify Plus
- **Unlimited custom fields** on all our plans
- **Industry-specific templates** for quick setup
- **Native Shopify admin integration**

### ROI Calculator
| Your Current Plan | Shopify Plus | InventorySync | Monthly Savings | Annual Savings |
|-------------------|--------------|---------------|-----------------|----------------|
| Basic ($39) | $2,000+ | $29 | $1,971 | $23,652 |
| Shopify ($105) | $2,000+ | $79 | $1,921 | $23,052 |
| Advanced ($399) | $2,000+ | $149 | $1,851 | $22,212 |

## Getting Started

### Step 1: Install the App
1. Visit the [InventorySync App Store listing](https://apps.shopify.com/inventorysync)
2. Click "Add app"
3. Approve the permissions
4. Complete the setup wizard

### Step 2: Access Custom Fields
There are three ways to access custom fields:

#### Option A: From Product Pages
1. Go to **Products** in your Shopify admin
2. Select any product
3. Scroll down to the **InventorySync Custom Fields** section
4. Click **Manage Custom Fields**

#### Option B: From the App
1. Click **Apps** in your Shopify admin
2. Select **InventorySync**
3. Navigate to **Custom Fields**

#### Option C: Direct Link
Bookmark this link: `https://inventorysync.prestigecorp.au/custom-fields`

### Step 3: Create Your First Field
1. Click **Add Custom Field**
2. Enter field details:
   - **Name**: Display name (e.g., "Material")
   - **Key**: Unique identifier (e.g., "material")
   - **Type**: Select field type
   - **Description**: Help text for your team
3. Click **Save**

## Industry Templates

Get started instantly with pre-built templates designed for your industry:

### Fashion & Apparel 👕
Perfect for clothing, shoes, and accessories:
- Material composition
- Care instructions
- Fit type (slim, regular, relaxed)
- Season
- Country of origin

**Quick Apply**: Click **Templates** → **Fashion & Apparel** → **Apply**

### Electronics & Tech 💻
Essential fields for electronic products:
- Battery life
- Warranty period
- Technical specifications
- Compatibility list
- Certifications (FCC, CE, etc.)

**Quick Apply**: Click **Templates** → **Electronics & Tech** → **Apply**

### Food & Beverage 🍔
Track important food information:
- Ingredients list
- Allergen warnings
- Nutritional information
- Best before dates
- Storage instructions

**Quick Apply**: Click **Templates** → **Food & Beverage** → **Apply**

### Beauty & Cosmetics 💄
Manage beauty product details:
- Full ingredient list (INCI)
- Skin type compatibility
- Usage instructions
- Volume/size
- Cruelty-free status

**Quick Apply**: Click **Templates** → **Beauty & Cosmetics** → **Apply**

### Home & Garden 🏠
Track home product specifications:
- Dimensions (L x W x H)
- Assembly requirements
- Material composition
- Care instructions
- Weight capacity

**Quick Apply**: Click **Templates** → **Home & Garden** → **Apply**

## Managing Custom Fields

### Adding Fields to Products

1. **Individual Products**:
   - Open any product
   - Find the Custom Fields section
   - Enter values for each field
   - Click **Save**

2. **Multiple Products**:
   - Go to **InventorySync** → **Bulk Operations**
   - Select products
   - Choose fields to update
   - Enter values
   - Click **Apply to All**

### Organizing Fields

**Field Groups**: Organize related fields together
- Create groups like "Specifications", "Compliance", "Marketing"
- Drag and drop to reorder
- Collapse/expand groups for cleaner interface

**Field Order**: Arrange fields logically
- Most important fields first
- Group related information
- Hide rarely-used fields

### Field Validation

Set rules to ensure data quality:
- **Required fields**: Must be filled before saving
- **Format validation**: Email, URL, phone number formats
- **Number ranges**: Min/max values for numeric fields
- **Character limits**: Maximum length for text fields
- **Custom patterns**: Regular expressions for advanced validation

## Field Types

### Text Fields 📝
- **Single Line**: Product codes, SKUs, short descriptions
- **Multi Line**: Detailed descriptions, care instructions
- **Rich Text**: Formatted content with bold, italic, lists

### Numeric Fields 🔢
- **Integer**: Whole numbers (quantity, count)
- **Decimal**: Prices, weights, measurements
- **Percentage**: Discount rates, composition percentages

### Date & Time 📅
- **Date**: Expiry dates, launch dates
- **Date & Time**: Precise timestamps
- **Date Range**: Season availability, promotional periods

### Selection Fields ✅
- **Dropdown**: Single selection from list
- **Multi-select**: Multiple options (features, categories)
- **Boolean**: Yes/No toggles

### Special Fields 🌟
- **Color**: Color picker for product colors
- **File**: Attach PDFs, certificates, manuals
- **URL**: Links to resources, videos
- **JSON**: Complex structured data

## Bulk Operations

### Bulk Edit
1. Go to **InventorySync** → **Bulk Operations**
2. Filter products:
   - By collection
   - By vendor
   - By product type
   - By custom field values
3. Select products to update
4. Choose operation:
   - **Set Value**: Apply same value to all
   - **Find & Replace**: Replace text across products
   - **Append/Prepend**: Add text before/after existing values
   - **Clear**: Remove values
5. Preview changes
6. Click **Apply**

### Bulk Import
1. Download the CSV template
2. Fill in your data
3. Upload the CSV
4. Map columns to fields
5. Preview import
6. Click **Import**

**Pro Tips**:
- Use Excel/Google Sheets for easier editing
- Test with a small batch first
- Keep backups before major changes

## Import/Export

### Exporting Data

**Quick Export**:
1. Click **Export** button
2. Choose format (CSV or JSON)
3. Select fields to include
4. Download file

**Scheduled Exports**:
- Set up daily/weekly exports
- Automatically email reports
- Sync with Google Drive/Dropbox

### Importing Data

**From CSV**:
1. Prepare your CSV with headers matching field keys
2. Click **Import** → **From CSV**
3. Upload file
4. Map columns
5. Review and confirm

**From Other Systems**:
- Shopify CSV export
- Excel/Google Sheets
- ERP systems
- Previous metafield apps

### API Access
For developers and advanced users:
```
GET /api/metafields/values/{product_id}
POST /api/metafields/values
PUT /api/metafields/bulk
```

## FAQ

### How is this different from Shopify's native metafields?
- **More field types**: We support 15+ field types vs Shopify's basic types
- **Better UI**: User-friendly interface designed for merchants
- **Templates**: Industry-specific quick-start templates
- **Bulk operations**: Update thousands of products at once
- **Import/Export**: Full data portability
- **Cost**: Save $1,971/month vs Shopify Plus

### Will my data be safe?
Yes! We:
- Store data securely on enterprise-grade servers
- Perform daily backups
- Use encryption for sensitive data
- Are GDPR compliant
- Never share your data

### Can I migrate from Shopify Plus?
Absolutely! We provide:
- Free migration assistance
- Data import tools
- Field mapping support
- No downtime during migration

### What happens if I cancel?
- Your data remains accessible for 30 days
- Export all data anytime
- No lock-in contracts
- Easy reactivation if you return

### Do custom fields show on my storefront?
Yes! Custom fields can be:
- Displayed on product pages
- Used in search/filtering
- Included in product feeds
- Accessed via Storefront API

## Support

### Getting Help

**Documentation**: [docs.inventorysync.app](https://docs.inventorysync.app)

**Email Support**: 
- Starter Plan: support@inventorysync.app (24-48 hour response)
- Growth Plan: priority@inventorysync.app (12-24 hour response)
- Pro Plan: dedicated@inventorysync.app (2-4 hour response)

**Live Chat**: Available on Growth and Pro plans

**Video Tutorials**: [youtube.com/inventorysync](https://youtube.com/inventorysync)

### Feature Requests
We love feedback! Submit ideas at ideas.inventorysync.app

### Community
- Join our [Facebook Group](https://facebook.com/groups/inventorysync)
- Follow us on [Twitter](https://twitter.com/inventorysync)
- Read our [Blog](https://blog.inventorysync.app)

---

## Ready to Save $1,971/month?

Stop overpaying for custom fields. Join thousands of smart merchants who've made the switch.

[**Start Your 14-Day Free Trial →**](https://inventorysync.prestigecorp.au)

*No credit card required. Set up in minutes. Cancel anytime.*
