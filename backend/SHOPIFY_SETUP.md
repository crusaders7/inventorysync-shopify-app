# Shopify OAuth Integration Setup

This document provides comprehensive instructions for setting up Shopify OAuth authentication for InventorySync.

## Overview

InventorySync integrates with Shopify using OAuth 2.0 for secure authentication and API access. The implementation includes:
- **Enhanced security** with HMAC verification
- **Comprehensive logging** of all authentication events
- **Webhook support** for real-time updates
- **Production-ready** error handling and validation

## Quick Start

### 1. Create Shopify App

1. **Go to Shopify Partners Dashboard**
   - Visit: https://partners.shopify.com/
   - Sign in or create a partner account

2. **Create a New App**
   - Click "Apps" → "Create app" → "Create app manually"
   - App name: `InventorySync`
   - App URL: `https://yourdomain.com` (or `http://localhost:8000` for development)

3. **Configure App URLs**
   - **App URL**: `https://yourdomain.com`
   - **Allowed redirection URL(s)**: `https://yourdomain.com/api/v1/auth/callback`
   - For development: `http://localhost:8000/api/v1/auth/callback`

4. **Set Required Scopes**
   The app automatically requests these scopes:
   - `read_products` - Read product information
   - `write_products` - Modify products
   - `read_inventory` - Read inventory levels
   - `write_inventory` - Update inventory levels
   - `read_locations` - Access store locations
   - `read_orders` - Read order data for analytics
   - `read_analytics` - Access analytics data

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and update:

```bash
# Shopify App Configuration
SHOPIFY_API_KEY=your_32_character_api_key
SHOPIFY_API_SECRET=your_32_character_secret_key
SHOPIFY_WEBHOOK_SECRET=your_webhook_secret

# App URLs
APP_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

### 3. Test Authentication

1. **Start the backend server:**
   ```bash
   python -m uvicorn main:app --reload
   ```

2. **Check auth status:**
   ```bash
   curl http://localhost:8000/api/v1/auth/status
   ```

3. **Test installation flow:**
   - Visit: `http://localhost:8000/api/v1/auth/install?shop=yourstore.myshopify.com`
   - Complete OAuth flow
   - Verify store is saved in database

## Authentication Flow

### 1. Installation Process

```mermaid
sequenceDiagram
    participant User
    participant InventorySync
    participant Shopify
    participant Database

    User->>InventorySync: Visit /auth/install?shop=store.myshopify.com
    InventorySync->>InventorySync: Validate shop domain
    InventorySync->>InventorySync: Generate secure state token
    InventorySync->>Shopify: Redirect to OAuth authorization
    Shopify->>User: Show permission request
    User->>Shopify: Approve permissions
    Shopify->>InventorySync: Callback with authorization code
    InventorySync->>InventorySync: Verify state & HMAC
    InventorySync->>Shopify: Exchange code for access token
    InventorySync->>Shopify: Fetch store & location info
    InventorySync->>Database: Save store and locations
    InventorySync->>User: Redirect to app dashboard
```

### 2. API Request Flow

```mermaid
sequenceDiagram
    participant Frontend
    participant InventorySync
    participant Shopify
    
    Frontend->>InventorySync: API request with shop parameter
    InventorySync->>Database: Get access token for shop
    InventorySync->>Shopify: Make authenticated API call
    Shopify->>InventorySync: Return data
    InventorySync->>Frontend: Return processed data
```

## Security Features

### 1. HMAC Verification

All Shopify requests are verified using HMAC-SHA256:

```python
def verify_shopify_hmac(query_params: Dict[str, str], api_secret: str) -> bool:
    """Verify Shopify HMAC signature"""
    if 'hmac' not in query_params:
        return False
    
    hmac_to_verify = query_params.pop('hmac')
    sorted_params = sorted(query_params.items())
    query_string = "&".join([f"{k}={v}" for k, v in sorted_params])
    
    calculated_hmac = hmac.new(
        api_secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(calculated_hmac, hmac_to_verify)
```

### 2. State Parameter Protection

- Cryptographically secure state tokens prevent CSRF attacks
- State tokens are validated on callback
- Tokens expire after 5 minutes (in production with Redis)

### 3. Access Token Security

- Tokens are securely stored in the database
- Encrypted in production environments
- Automatic token refresh (if supported by Shopify)
- Token validation before API calls

## Webhook Integration

### 1. Webhook Setup

InventorySync supports real-time updates via webhooks:

```python
# Webhook topics handled:
WEBHOOK_TOPICS = [
    "products/create",
    "products/update", 
    "inventory_levels/update",
    "app/uninstalled"
]
```

### 2. Webhook Verification

All webhooks are verified using HMAC-SHA256:

```python
def verify_webhook(data: bytes, hmac_header: str, webhook_secret: str) -> bool:
    calculated_hmac = base64.b64encode(
        hmac.new(
            webhook_secret.encode('utf-8'),
            data,
            hashlib.sha256
        ).digest()
    ).decode()
    
    return hmac.compare_digest(calculated_hmac, hmac_header)
```

### 3. Webhook Handlers

```python
@router.post("/webhook")
async def shopify_webhook(request: Request):
    # Verify authenticity
    # Process webhook based on topic
    # Update local database
    # Log activity
```

## API Endpoints

### Authentication Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/install` | GET | Start OAuth installation flow |
| `/api/v1/auth/callback` | GET | OAuth callback handler |
| `/api/v1/auth/status` | GET | Check authentication status |
| `/api/v1/auth/logout` | POST | Remove store access |

### Protected Endpoints

All other API endpoints require authentication via shop parameter:

```
GET /api/v1/inventory?shop=yourstore.myshopify.com
```

## Troubleshooting

### Common Issues

1. **HMAC Verification Fails**
   - Ensure API secret is correct
   - Check query parameter encoding
   - Verify timestamp is recent

2. **OAuth Callback Errors**
   - Confirm redirect URLs match exactly
   - Check state parameter handling
   - Verify shop domain format

3. **API Rate Limiting**
   - Implement exponential backoff
   - Cache frequently accessed data
   - Use bulk operations where possible

### Logging

Enable debug logging to troubleshoot issues:

```python
# In .env
LOG_LEVEL=DEBUG
```

Check logs at:
- `backend/logs/app.log`
- `backend/logs/auth.log`

## Production Deployment

### Security Checklist

- [ ] Use HTTPS for all URLs
- [ ] Enable database encryption
- [ ] Set strong secret keys
- [ ] Configure webhook verification
- [ ] Implement rate limiting
- [ ] Enable comprehensive logging
- [ ] Set up monitoring alerts

### Environment Variables

```bash
# Production settings
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@host/db
REDIS_URL=redis://localhost:6379
SECRET_KEY=strong_random_secret_key
```

## Support

For issues or questions:
- Check the [API Documentation](./docs/API_DOCUMENTATION.md)
- Review authentication logs
- Contact support with shop domain and timestamp
