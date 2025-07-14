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
SHOPIFY_WEBHOOK_SECRET=your_webhook_secret [REDACTED]

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
| `/api/v1/auth/install` | GET | Initiate OAuth flow |
| `/api/v1/auth/callback` | GET | Handle OAuth callback |
| `/api/v1/auth/status` | GET | Check auth configuration |
| `/api/v1/auth/webhook` | POST | Handle Shopify webhooks |

### Installation Flow

```bash
# 1. Start installation
GET /api/v1/auth/install?shop=store.myshopify.com

# 2. User completes OAuth on Shopify
# 3. Callback received
GET /api/v1/auth/callback?shop=store.myshopify.com&code=...&state=...

# 4. Check status
GET /api/v1/auth/status
```

## Error Handling

### Common Error Scenarios

1. **Invalid Shop Domain**
   ```json
   {
     "error": "Invalid shop domain format",
     "details": {"field": "shop"},
     "type": "validation_error"
   }
   ```

2. **Authentication Failed**
   ```json
   {
     "error": "Shopify authentication failed",
     "details": {"reason": "invalid_code"},
     "type": "authentication_error"
   }
   ```

3. **Rate Limit Exceeded**
   ```json
   {
     "error": "Shopify API rate limit exceeded",
     "details": {"retry_after": 60},
     "type": "rate_limit_error"
   }
   ```

### Error Recovery

- **Automatic retry** for transient errors
- **Exponential backoff** for rate limiting
- **Comprehensive logging** for debugging
- **User-friendly error messages**

## Development Setup

### 1. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your Shopify app credentials

# Initialize database
python database_manager.py --init --seed

# Start server
python -m uvicorn main:app --reload

# Test authentication
curl "http://localhost:8000/api/v1/auth/status"
```

### 2. ngrok Setup (for webhooks)

```bash
# Install ngrok
npm install -g ngrok

# Expose local server
ngrok http 8000

# Update Shopify app settings with ngrok URL
# App URL: https://abc123.ngrok.io
# Callback URL: https://abc123.ngrok.io/api/v1/auth/callback
```

### 3. Testing OAuth Flow

```bash
# 1. Visit installation URL
open "http://localhost:8000/api/v1/auth/install?shop=yourstore.myshopify.com"

# 2. Complete OAuth on Shopify

# 3. Verify store was saved
python database_manager.py --health
```

## Production Deployment

### 1. Environment Configuration

```bash
# Production environment variables
ENVIRONMENT=production
DEBUG=false
APP_URL=https://yourdomain.com
FRONTEND_URL=https://app.yourdomain.com

# Secure secrets
SHOPIFY_API_KEY=your_production_api_key
SHOPIFY_API_SECRET=your_production_secret
SHOPIFY_WEBHOOK_SECRET=your_webhook_secret
SECRET_KEY=your_256_bit_jwt_secret

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/inventorysync

# Redis for state management
REDIS_URL=redis://:password@localhost:6379/0
```

### 2. SSL Configuration

- **SSL certificate** required for production
- **HTTPS URLs** in Shopify app settings
- **Secure cookie settings** for sessions

### 3. Monitoring

```bash
# Health check endpoints
GET /health
GET /api/v1/auth/status

# Log monitoring
tail -f logs/inventorysync.log

# Database health
python database_manager.py --health
```

## Security Best Practices

### 1. Credential Management

- **Never commit** API keys to version control
- **Use environment variables** for all secrets
- **Rotate credentials** regularly
- **Use different keys** for development/production

### 2. Access Control

- **Validate all inputs** before processing
- **Use HTTPS** for all communications
- **Implement rate limiting** for API endpoints
- **Log security events** for monitoring

### 3. Data Protection

- **Encrypt sensitive data** at rest
- **Use secure connections** to Shopify
- **Implement proper session management**
- **Regular security audits**

## Troubleshooting

### Common Issues

1. **"Invalid API key format"**
   - Check that API key is exactly 32 characters
   - Verify no extra spaces or characters

2. **"HMAC verification failed"**
   - Ensure webhook secret matches Shopify settings
   - Check that request body is unmodified

3. **"Shop domain validation failed"**
   - Verify shop domain includes `.myshopify.com`
   - Check for typos in shop name

4. **"Database connection failed"**
   - Run: `python database_manager.py --health`
   - Check database URL in environment

### Debug Steps

```bash
# 1. Check configuration
python database_manager.py --info

# 2. Verify auth status
curl http://localhost:8000/api/v1/auth/status

# 3. Check logs
tail -f logs/inventorysync.log

# 4. Test database
python database_manager.py --health

# 5. Validate environment
python -c "from config import settings; print(settings.dict())"
```

## Support

For additional help:
- Check application logs: `logs/inventorysync.log`
- Review Shopify API documentation: https://shopify.dev/docs
- Test with Shopify's OAuth tool: https://shopify.dev/tools/oauth
- Monitor webhook deliveries in Shopify Partners dashboard

This authentication system provides enterprise-grade security and reliability for Shopify app integration.