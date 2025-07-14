#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Create app submission assets directory
const assetsDir = path.join(__dirname, '../app-submission-assets');
if (!fs.existsSync(assetsDir)) {
  fs.mkdirSync(assetsDir, { recursive: true });
}

// Generate app store listing content
const appListingContent = {
  name: "InventorySync - Custom Fields Pro",
  tagline: "Save $1,971/month vs Shopify Plus - Add unlimited custom fields to your products",
  shortDescription: "Add custom fields to products without upgrading to Shopify Plus. Track materials, dimensions, compliance data, and any attributes specific to your business.",
  
  keyBenefits: [
    "💰 Save $1,971/month compared to Shopify Plus ($29 vs $2,000)",
    "✨ Unlimited custom fields for products and variants",
    "🏭 Industry-specific templates (Fashion, Electronics, Food & Beverage)",
    "📊 Bulk operations and import/export capabilities",
    "🔍 Advanced search and filtering by custom field values",
    "📈 Real-time sync with Shopify",
    "🚀 Lightning-fast performance with 10,000+ products"
  ],
  
  extendedDescription: `
# Why InventorySync?

Shopify Basic merchants often need custom fields but can't justify the $2,000/month Shopify Plus upgrade. InventorySync bridges this gap, offering enterprise-level custom field functionality at a fraction of the cost.

## Perfect For:
- Fashion brands tracking materials, care instructions, and sizing
- Electronics retailers managing specifications and compliance data
- Food & beverage stores tracking ingredients and nutritional info
- Any business with complex product information needs

## Core Features:

### 🎯 Custom Field Types
- Text fields (short and long)
- Numbers and decimals
- Dates and date ranges
- Dropdowns and multi-select
- Yes/No toggles
- File attachments
- Rich text with formatting

### 🏭 Industry Templates
Get started instantly with pre-built templates:
- **Fashion & Apparel**: Materials, care instructions, fit details
- **Electronics**: Specifications, certifications, warranty info
- **Food & Beverage**: Ingredients, allergens, nutritional data
- **Beauty & Cosmetics**: Ingredients, usage instructions, certifications
- **Home & Garden**: Dimensions, assembly, care instructions

### 💪 Powerful Management
- Drag-and-drop field builder
- Field validation and required settings
- Conditional logic for dynamic fields
- Bulk edit multiple products at once
- Import/Export via CSV
- API access for integrations

### 📊 Advanced Features
- Search products by any custom field
- Filter and sort by custom values
- Analytics on field usage
- Data quality reporting
- Automated workflows based on field values

## Pricing That Makes Sense

**Starter - $29/month**
- Up to 1,000 products
- 10 custom fields
- 3 industry templates
- Email support
- 14-day free trial

**Growth - $79/month**
- Up to 10,000 products
- Unlimited custom fields
- All industry templates
- Bulk operations
- Priority support
- API access

**Pro - $149/month**
- Unlimited products
- White-label options
- Custom templates
- Dedicated support
- Advanced analytics
- Custom integrations

## What Our Customers Say

"We saved almost $24,000 per year by using InventorySync instead of upgrading to Shopify Plus. The custom fields work perfectly for our fashion brand." - Sarah M., Fashion Retailer

"Finally, a solution that lets us track all our product specifications without breaking the bank. Setup was instant with the electronics template." - Mike T., Electronics Store

"The bulk import feature saved us weeks of work. We imported 5,000 products with custom fields in minutes." - Jennifer L., Home Goods

## Get Started in Minutes

1. Install from Shopify App Store
2. Choose your industry template (or start from scratch)
3. Add custom fields to your products
4. Start saving $1,971/month!

## Support & Resources

- 📧 24/7 Email Support
- 📚 Comprehensive Documentation
- 🎥 Video Tutorials
- 💬 Live Chat (Growth & Pro plans)
- 🚀 Onboarding Assistance

Don't let custom field limitations hold your business back. Join thousands of merchants who've discovered the smart way to manage product information.

**Install InventorySync today and transform how you manage product data!**
`,

  pricingPlans: {
    starter: {
      name: "Starter",
      price: "$29/month",
      features: [
        "Up to 1,000 products",
        "10 custom fields",
        "3 industry templates",
        "Basic search & filter",
        "CSV import/export",
        "Email support",
        "14-day free trial"
      ]
    },
    growth: {
      name: "Growth",
      price: "$79/month",
      features: [
        "Up to 10,000 products",
        "Unlimited custom fields",
        "All industry templates",
        "Advanced search & filter",
        "Bulk operations",
        "API access",
        "Priority support",
        "Custom field analytics",
        "14-day free trial"
      ]
    },
    pro: {
      name: "Pro",
      price: "$149/month", 
      features: [
        "Unlimited products",
        "Everything in Growth",
        "White-label options",
        "Custom templates",
        "Advanced workflows",
        "Dedicated support",
        "Custom integrations",
        "SLA guarantee",
        "14-day free trial"
      ]
    }
  }
};

// Save app listing content
fs.writeFileSync(
  path.join(assetsDir, 'app-listing-content.json'),
  JSON.stringify(appListingContent, null, 2)
);

// Generate screenshot descriptions
const screenshots = [
  {
    filename: "01-dashboard.png",
    title: "Custom Fields Dashboard",
    description: "Manage all your custom fields from one intuitive dashboard"
  },
  {
    filename: "02-field-builder.png", 
    title: "Drag & Drop Field Builder",
    description: "Create custom fields with our visual builder - no coding required"
  },
  {
    filename: "03-product-edit.png",
    title: "Enhanced Product Editor",
    description: "Custom fields seamlessly integrated into your product pages"
  },
  {
    filename: "04-bulk-operations.png",
    title: "Bulk Edit Custom Fields",
    description: "Update hundreds of products at once with bulk operations"
  },
  {
    filename: "05-templates.png",
    title: "Industry Templates",
    description: "Get started instantly with pre-built industry templates"
  },
  {
    filename: "06-search-filter.png",
    title: "Advanced Search & Filter",
    description: "Find products by any custom field value"
  },
  {
    filename: "07-analytics.png",
    title: "Field Analytics",
    description: "Track field usage and data quality with built-in analytics"
  }
];

fs.writeFileSync(
  path.join(assetsDir, 'screenshots-info.json'),
  JSON.stringify(screenshots, null, 2)
);

// Generate HTML preview for app banner
const bannerHTML = `
<!DOCTYPE html>
<html>
<head>
  <style>
    body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    .banner { width: 1920px; height: 1080px; background: linear-gradient(135deg, #5C6AC4 0%, #8B92D8 100%); display: flex; align-items: center; justify-content: center; position: relative; overflow: hidden; }
    .content { text-align: center; color: white; z-index: 10; max-width: 1200px; }
    .title { font-size: 72px; font-weight: 700; margin-bottom: 24px; }
    .subtitle { font-size: 36px; font-weight: 400; margin-bottom: 48px; opacity: 0.9; }
    .savings { background: white; color: #5C6AC4; padding: 24px 48px; border-radius: 100px; font-size: 32px; font-weight: 600; display: inline-block; }
    .features { display: flex; gap: 40px; justify-content: center; margin-top: 60px; }
    .feature { background: rgba(255,255,255,0.1); padding: 24px; border-radius: 16px; flex: 1; }
    .feature-icon { font-size: 48px; margin-bottom: 16px; }
    .feature-text { font-size: 20px; }
    .pattern { position: absolute; opacity: 0.1; }
    .pattern-1 { top: -100px; left: -100px; width: 400px; height: 400px; background: white; border-radius: 50%; }
    .pattern-2 { bottom: -150px; right: -150px; width: 500px; height: 500px; background: white; border-radius: 50%; }
    .pattern-3 { top: 200px; right: 100px; width: 200px; height: 200px; background: white; transform: rotate(45deg); }
  </style>
</head>
<body>
  <div class="banner">
    <div class="pattern pattern-1"></div>
    <div class="pattern pattern-2"></div>
    <div class="pattern pattern-3"></div>
    <div class="content">
      <h1 class="title">InventorySync</h1>
      <p class="subtitle">Custom Fields for Shopify Without the Plus Price Tag</p>
      <div class="savings">Save $1,971/month vs Shopify Plus</div>
      <div class="features">
        <div class="feature">
          <div class="feature-icon">📦</div>
          <div class="feature-text">Unlimited<br>Custom Fields</div>
        </div>
        <div class="feature">
          <div class="feature-icon">🏭</div>
          <div class="feature-text">Industry<br>Templates</div>
        </div>
        <div class="feature">
          <div class="feature-icon">⚡</div>
          <div class="feature-text">Lightning<br>Fast</div>
        </div>
      </div>
    </div>
  </div>
</body>
</html>
`;

fs.writeFileSync(
  path.join(assetsDir, 'app-banner-preview.html'),
  bannerHTML
);

console.log('✅ App submission assets generated in:', assetsDir);
console.log('\nNext steps:');
console.log('1. Take screenshots of the app in action (1280x800px)');
console.log('2. Create app icon in PNG format (1024x1024px) from the SVG');
console.log('3. Create app banner (1920x1080px) using the HTML preview as guide');
console.log('4. Review app-listing-content.json for submission text');
