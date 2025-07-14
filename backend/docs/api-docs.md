# InventorySync API Documentation

## Overview

InventorySync provides a comprehensive REST API for managing inventory, custom fields, workflows, alerts, and integrations. The API offers enterprise-level inventory management features at an affordable price.

**Base URL**: `https://your-inventorysync-domain.com/api`

## Endpoints

### Authentication

Authentication is required for all API requests using either Shopify Session (for embedded app use) or API Key (for third-party integrations).

```http
GET /api/v1/auth/install
Content-Type: application/json
```

### Custom Fields API

Manage custom fields with full validation and industry templates.

#### Create Custom Field
```http
POST /api/custom-fields/{shop_domain}
```
**Request Body:**
```json
{
  "field_name": "season",
  "display_name": "Product Season",
  "field_type": "select",
  "target_entity": "product",
  "validation_rules": { "options": ["Spring", "Summer", "Fall", "Winter"] },
  "is_required": true
}
```

### Error Handling

Consistent error responses are provided for all API endpoints.

#### Error Response Format
```json
{
  "error": "Validation failed",
  "details": [
    { "field": "field_name", "message": "Field name is required" }
  ],
  "type": "validation_error",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Rate Limiting

API requests are rate limited based on your plan:
- **Starter**: 500/hour, 50/minute
- **Growth**: 2000/hour, 200/minute
- **Pro**: 10000/hour, 1000/minute

Rate limit headers are included in all responses:
```http
X-RateLimit-Limit: 500
X-RateLimit-Remaining: 487
X-RateLimit-Reset: 1642248000
```

## Webhooks

InventorySync supports webhooks for real-time notifications:

### Supported Events
- `product.created`
- `product.updated`
- `inventory.updated`
- `alert.created`

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

This documentation provides the necessary information for developers to interact with the InventorySync API effectively.
