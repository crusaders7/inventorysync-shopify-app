# InventorySync API Documentation

## Overview

InventorySync provides a comprehensive REST API for managing inventory, custom fields, workflows, alerts, and integrations. Our API is designed for developers who need enterprise-level inventory management features at an affordable price point.

**Base URL**: `https://your-inventorysync-domain.com/api`

## Authentication

All API requests require authentication using either:

1. **Shopify Session** (for embedded app use)
2. **API Key** (for third-party integrations)

### API Key Authentication
```http
GET /api/products
X-API-Key: isk_your_api_key_here
Content-Type: application/json
```

## Quick Start

### 1. Get Store Information
```http
GET /api/dashboard/test-store.myshopify.com
```

### 2. Create Custom Fields
```http
POST /api/custom-fields/test-store.myshopify.com
Content-Type: application/json

{
  "field_name": "season",
  "display_name": "Product Season",
  "field_type": "select",
  "target_entity": "product",
  "validation_rules": {
    "options": ["Spring", "Summer", "Fall", "Winter"]
  },
  "is_required": true
}
```

### 3. Build Custom Reports
```http
POST /api/reports/test-store.myshopify.com/build
Content-Type: application/json

{
  "name": "Seasonal Inventory Report",
  "entity_type": "product",
  "metrics": [
    {
      "field": "id",
      "aggregation": "count",
      "label": "Product Count"
    },
    {
      "field": "price",
      "aggregation": "avg",
      "label": "Average Price"
    }
  ],
  "group_by": ["custom_field"],
  "filters": [
    {
      "field": "custom_data.season",
      "operator": "equals",
      "value": "Winter"
    }
  ]
}
```

---

## Core Endpoints

### Custom Fields API

Manage dynamic custom fields for any entity type with full validation and industry templates.

#### Create Custom Field
```http
POST /api/custom-fields/{shop_domain}
```

**Request Body:**
```json
{
  "field_name": "material_type",
  "display_name": "Material Type", 
  "field_type": "select",
  "target_entity": "product",
  "validation_rules": {
    "options": ["Cotton", "Polyester", "Wool", "Silk"]
  },
  "is_required": false,
  "is_searchable": true,
  "field_group": "basic",
  "industry_template": "fashion"
}
```

**Response:**
```json
{
  "id": 123,
  "field_name": "material_type",
  "display_name": "Material Type",
  "field_type": "select",
  "target_entity": "product",
  "validation_rules": {
    "options": ["Cotton", "Polyester", "Wool", "Silk"]
  },
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Get Custom Fields
```http
GET /api/custom-fields/{shop_domain}?entity_type=product&include_inactive=false
```

**Response:**
```json
{
  "fields": [
    {
      "id": 123,
      "field_name": "material_type",
      "display_name": "Material Type",
      "field_type": "select",
      "target_entity": "product",
      "validation_rules": {
        "options": ["Cotton", "Polyester", "Wool", "Silk"]
      },
      "usage_count": 45,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total_count": 1
}
```

#### Apply Industry Template
```http
POST /api/custom-fields/{shop_domain}/templates/fashion
```

**Response:**
```json
{
  "template": "fashion",
  "fields_created": 12,
  "message": "Fashion industry template applied successfully",
  "fields": [
    {"field_name": "season", "display_name": "Season"},
    {"field_name": "size", "display_name": "Size"},
    {"field_name": "color", "display_name": "Color"},
    {"field_name": "material", "display_name": "Material"}
  ]
}
```

---

### Enhanced Alerts API

Powerful alerting system with custom templates, analytics, and auto-resolution.

#### Create Alert
```http
POST /api/alerts/{shop_domain}
```

**Request Body:**
```json
{
  "alert_type": "low_stock",
  "severity": "high", 
  "title": "Critical Stock Alert",
  "message": "Stock for {sku} is critically low at {current_stock} units",
  "product_sku": "SHIRT-001",
  "location_name": "Main Warehouse",
  "current_stock": 2,
  "recommended_action": "Reorder immediately - lead time 7 days",
  "notification_channels": ["email", "webhook"],
  "auto_resolve_hours": 24
}
```

**Response:**
```json
{
  "id": 456,
  "alert_type": "low_stock",
  "severity": "high",
  "title": "Critical Stock Alert", 
  "message": "Alert 'Critical Stock Alert' created successfully"
}
```

#### Get Alerts with Advanced Filtering
```http
GET /api/alerts/{shop_domain}?status=active&severity=high&alert_type=low_stock&limit=50&sort_by=created_at&sort_order=desc
```

**Response:**
```json
{
  "alerts": [
    {
      "id": 456,
      "alert_type": "low_stock",
      "severity": "high",
      "title": "Critical Stock Alert",
      "message": "Stock for SHIRT-001 is critically low at 2 units",
      "product_sku": "SHIRT-001",
      "current_stock": 2,
      "is_acknowledged": false,
      "is_resolved": false,
      "auto_resolve_at": "2024-01-16T10:30:00Z",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total_count": 1,
  "has_more": false
}
```

#### Get Alert Analytics
```http
GET /api/alerts/analytics/{shop_domain}?days=30
```

**Response:**
```json
{
  "period_days": 30,
  "summary": {
    "total_alerts": 145,
    "resolved_alerts": 132,
    "acknowledged_alerts": 140,
    "active_alerts": 13,
    "resolution_rate": 91.0
  },
  "breakdown": {
    "by_type": [
      {"alert_type": "low_stock", "count": 78},
      {"alert_type": "overstock", "count": 34},
      {"alert_type": "compliance", "count": 33}
    ],
    "by_severity": [
      {"severity": "high", "count": 45},
      {"severity": "medium", "count": 67},
      {"severity": "low", "count": 33}
    ]
  }
}
```

---

### Workflow Automation API

Event-driven automation engine with complex condition evaluation and multiple action types.

#### Create Workflow Rule
```http
POST /api/workflows/rules/{shop_domain}
```

**Request Body:**
```json
{
  "rule_name": "Seasonal Product Automation",
  "description": "Automatically adjust pricing for seasonal items",
  "trigger_event": "custom_field_change",
  "trigger_conditions": {
    "type": "and",
    "conditions": [
      {
        "field": "field_name",
        "operator": "equals", 
        "value": "season"
      },
      {
        "field": "new_value",
        "operator": "equals",
        "value": "Winter"
      }
    ]
  },
  "actions": [
    {
      "type": "update_field",
      "entity_type": "product",
      "field_name": "priority",
      "value": "high"
    },
    {
      "type": "create_alert",
      "title": "Seasonal Product Updated",
      "message": "Product {entity_id} marked as Winter seasonal item",
      "severity": "info"
    }
  ],
  "priority": 100,
  "is_active": true
}
```

#### Test Workflow Rule
```http
POST /api/workflows/rules/{rule_id}/test?shop_domain={shop_domain}
```

**Request Body:**
```json
{
  "field_name": "season",
  "new_value": "Winter",
  "old_value": "Fall",
  "entity_id": 123,
  "entity_type": "product"
}
```

**Response:**
```json
{
  "rule_name": "Seasonal Product Automation",
  "conditions_met": true,
  "test_data": {
    "field_name": "season",
    "new_value": "Winter"
  },
  "would_execute": true
}
```

---

### Custom Reports API

Build reports on any field with advanced aggregations, grouping, and filtering.

#### Build Custom Report
```http
POST /api/reports/{shop_domain}/build?export_format=json
```

**Request Body:**
```json
{
  "name": "Inventory Value by Location", 
  "entity_type": "inventory",
  "metrics": [
    {
      "field": "available_quantity",
      "aggregation": "sum",
      "label": "Total Available"
    },
    {
      "field": "on_hand_quantity", 
      "aggregation": "sum",
      "label": "Total On Hand"
    }
  ],
  "group_by": ["location"],
  "filters": [
    {
      "field": "available_quantity",
      "operator": "greater_than",
      "value": 0
    }
  ],
  "sort_by": "Total Available",
  "sort_order": "desc",
  "limit": 100
}
```

**Response:**
```json
{
  "report_name": "Inventory Value by Location",
  "generated_at": "2024-01-15T10:30:00Z",
  "row_count": 3,
  "data": [
    {
      "location_id": 1,
      "Total Available": 1250,
      "Total On Hand": 1300
    },
    {
      "location_id": 2, 
      "Total Available": 890,
      "Total On Hand": 920
    }
  ],
  "metadata": {
    "entity_type": "inventory",
    "metrics": [
      {"field": "available_quantity", "aggregation": "sum"}
    ]
  }
}
```

#### Get Available Fields for Reporting
```http
GET /api/reports/{shop_domain}/fields/product
```

**Response:**
```json
{
  "entity_type": "product",
  "standard_fields": [
    {
      "field": "title",
      "label": "Product Title",
      "type": "text",
      "aggregations": ["count", "count_distinct"]
    },
    {
      "field": "price", 
      "label": "Price",
      "type": "number",
      "aggregations": ["sum", "avg", "min", "max"]
    }
  ],
  "custom_fields": [
    {
      "field": "custom_data.season",
      "label": "Season",
      "type": "select",
      "aggregations": ["count", "count_distinct"]
    }
  ],
  "total_fields": 12
}
```

---

### Integrations API

Third-party system connections with API keys, webhooks, and bulk operations.

#### Create API Key
```http
POST /api/integrations/{shop_domain}/api-keys
```

**Request Body:**
```json
{
  "name": "WMS Integration",
  "description": "Warehouse Management System sync",
  "permissions": ["inventory:read", "inventory:write", "products:read"],
  "rate_limit": 1000,
  "expires_at": "2025-01-15T00:00:00Z"
}
```

**Response:**
```json
{
  "api_key": "isk_AbCdEf123456789",
  "api_secret": "secret_XyZ987654321",
  "name": "WMS Integration",
  "permissions": ["inventory:read", "inventory:write", "products:read"],
  "rate_limit": 1000,
  "created_at": "2024-01-15T10:30:00Z",
  "warning": "Store this API key securely. It will not be shown again."
}
```

#### Create Webhook
```http
POST /api/integrations/{shop_domain}/webhooks
```

**Request Body:**
```json
{
  "name": "Inventory Updates",
  "url": "https://your-system.com/webhooks/inventory",
  "events": ["inventory.updated", "product.created", "alert.created"],
  "headers": {
    "Authorization": "Bearer your-token"
  },
  "is_active": true
}
```

#### Sync External Data
```http
POST /api/integrations/{shop_domain}/sync
X-API-Key: isk_your_api_key_here
```

**Request Body:**
```json
{
  "entity_type": "inventory",
  "external_id": "WMS-INV-001",
  "data": {
    "available_quantity": 150,
    "on_hand_quantity": 160,
    "reorder_point": 25,
    "supplier_name": "ACME Supplier",
    "last_delivery": "2024-01-10"
  },
  "source_system": "WMS_v2.1"
}
```

#### Bulk Operations
```http
POST /api/integrations/{shop_domain}/bulk
X-API-Key: isk_your_api_key_here
```

**Request Body:**
```json
{
  "operation": "update",
  "entity_type": "inventory", 
  "data": [
    {
      "id": 123,
      "available_quantity": 45,
      "reorder_point": 20
    },
    {
      "id": 124,
      "available_quantity": 67,
      "reorder_point": 15
    }
  ],
  "options": {
    "validate_only": false,
    "send_notifications": true
  }
}
```

---

## Error Handling

All API endpoints return consistent error responses:

### Error Response Format
```json
{
  "error": "Validation failed",
  "details": [
    {
      "field": "field_name",
      "message": "Field name is required"
    }
  ],
  "type": "validation_error",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request / Validation Error
- `401` - Unauthorized
- `403` - Forbidden / Plan Limit Exceeded  
- `404` - Not Found
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

### Plan Limit Errors
```json
{
  "error": "Plan limit reached",
  "details": "Starter plan allows 5 custom fields. Upgrade to Growth plan for unlimited fields.",
  "type": "plan_limit_error",
  "upgrade_url": "/billing/upgrade",
  "current_plan": "starter"
}
```

---

## Rate Limiting

API requests are rate limited based on your plan:

| Plan | Rate Limit | Burst Limit |
|------|------------|-------------|
| Starter | 500/hour | 50/minute |
| Growth | 2000/hour | 200/minute |
| Pro | 10000/hour | 1000/minute |

Rate limit headers are included in all responses:
```http
X-RateLimit-Limit: 500
X-RateLimit-Remaining: 487
X-RateLimit-Reset: 1642248000
```

---

## Webhooks

InventorySync sends webhooks for real-time notifications:

### Supported Events
- `product.created`
- `product.updated` 
- `inventory.updated`
- `inventory.low_stock`
- `alert.created`
- `alert.resolved`
- `custom_field.changed`
- `workflow.executed`

### Webhook Payload Example
```json
{
  "event": "inventory.updated",
  "shop_domain": "test-store.myshopify.com",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "inventory_item_id": 123,
    "variant_id": 456,
    "location_id": 1,
    "old_quantity": 45,
    "new_quantity": 42,
    "change_reason": "sale"
  },
  "webhook_id": "wh_AbCdEf123"
}
```

### Webhook Security
Verify webhook authenticity using HMAC signatures:
```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

---

## SDK Examples

### JavaScript/Node.js
```javascript
const InventorySync = require('@inventorysync/api');

const client = new InventorySync({
  apiKey: 'isk_your_api_key',
  shopDomain: 'test-store.myshopify.com'
});

// Create custom field
const field = await client.customFields.create({
  field_name: 'priority',
  display_name: 'Product Priority',
  field_type: 'select',
  target_entity: 'product',
  validation_rules: {
    options: ['Low', 'Medium', 'High', 'Critical']
  }
});

// Build report
const report = await client.reports.build({
  name: 'High Priority Products',
  entity_type: 'product',
  metrics: [
    { field: 'id', aggregation: 'count', label: 'Product Count' }
  ],
  filters: [
    { field: 'custom_data.priority', operator: 'equals', value: 'High' }
  ]
});
```

### Python
```python
from inventorysync import InventorySyncAPI

client = InventorySyncAPI(
    api_key='isk_your_api_key',
    shop_domain='test-store.myshopify.com'
)

# Create workflow rule
rule = client.workflows.create_rule({
    'rule_name': 'Low Stock Alert',
    'trigger_event': 'inventory_low',
    'trigger_conditions': {
        'type': 'and',
        'conditions': [
            {'field': 'current_stock', 'operator': 'less_than', 'value': 10}
        ]
    },
    'actions': [
        {
            'type': 'create_alert',
            'title': 'Low Stock Alert',
            'message': 'Stock for {sku} is low: {current_stock} units',
            'severity': 'high'
        }
    ]
})
```

---

## Competitive Advantages

### vs Basic Tools ($300-500)
- ✅ **Unlimited Custom Fields** (vs 5-10 fixed fields)
- ✅ **Advanced Reporting** (vs basic CSV exports)  
- ✅ **Workflow Automation** (vs manual processes)
- ✅ **Real-time Analytics** (vs daily reports)

### vs Enterprise Solutions ($2,500+)
- ✅ **Same Feature Set** at 90% lower cost
- ✅ **Shopify Native** (vs external systems)
- ✅ **No Implementation Fees** (vs $10k+ setup)
- ✅ **Instant Setup** (vs 6-month implementations)

---

## Support

- **Documentation**: https://docs.inventorysync.com
- **API Support**: api-support@inventorysync.com  
- **Discord Community**: https://discord.gg/inventorysync
- **Status Page**: https://status.inventorysync.com

---

*API Version: 1.0.0 | Last Updated: January 2024*