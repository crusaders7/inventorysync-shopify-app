# Railway Environment Variables Setup Guide

## Required Environment Variables for Railway

Copy and paste these into your Railway dashboard. Replace placeholder values with your actual credentials.

### 1. Database Configuration

```
DATABASE_URL=postgresql://postgres:YOUR_POSTGRES_PASSWORD@postgres.railway.internal:5432/railway
DATABASE_URL_ASYNC=postgresql+asyncpg://postgres:YOUR_POSTGRES_PASSWORD@postgres.railway.internal:5432/railway
```

**Note**: Railway automatically provisions PostgreSQL with the internal hostname `postgres.railway.internal`. The database name is typically `railway`.

### 2. Redis Configuration

```
REDIS_URL=redis://default:YOUR_REDIS_PASSWORD@redis.railway.internal:6379
```

**Note**: Railway Redis uses `default` as the username and provides internal hostname `redis.railway.internal`.

### 3. Security Keys

```
SECRET_KEY=your-production-secret-key-must-be-very-secure-256-bit
JWT_SECRET_KEY=another-secure-key-for-jwt-tokens
ENCRYPTION_KEY=encryption-key-for-sensitive-data
```

**To generate secure keys, use this command:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Shopify App Configuration

```
SHOPIFY_API_KEY=your_shopify_api_key_from_partner_dashboard
SHOPIFY_API_SECRET=your_shopify_api_secret_from_partner_dashboard
SHOPIFY_WEBHOOK_SECRET=your_webhook_secret_from_partner_dashboard
```

### 5. Application URLs

```
APP_URL=https://reasonable-perfection.up.railway.app
FRONTEND_URL=https://reasonable-perfection.up.railway.app
BACKEND_URL=https://reasonable-perfection.up.railway.app
```

### 6. Application Settings

```
APP_NAME=InventorySync
APP_VERSION=1.0.0
APP_ENV=production
DEBUG=false
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000
```

### 7. CORS Configuration

```
CORS_ORIGINS=["https://reasonable-perfection.up.railway.app", "https://admin.shopify.com"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS=["*"]
ALLOWED_HOSTS=reasonable-perfection.up.railway.app,*.railway.app
```

### 8. Logging Configuration

```
LOG_LEVEL=INFO
LOG_FORMAT=json
ENABLE_REQUEST_VALIDATION=true
```

### 9. Performance Settings

```
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
REDIS_MAX_CONNECTIONS=50
REDIS_CACHE_TTL=3600
DATABASE_STATEMENT_TIMEOUT=30000
API_TIMEOUT=60
WORKERS=4
```

### 10. JWT Settings

```
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 11. Rate Limiting

```
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=120
RATE_LIMIT_DEFAULT=100/minute
RATE_LIMIT_BURST=20
DISABLE_RATE_LIMIT=false
```

### 12. Security Settings

```
SSL_REDIRECT=true
SECURE_COOKIES=true
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=lax
```

### 13. Feature Flags

```
ENABLE_FORECASTING=true
ENABLE_MULTI_LOCATION=true
ENABLE_SUPPLIER_INTEGRATION=true
ENABLE_CUSTOM_FIELDS=true
ENABLE_WORKFLOW_AUTOMATION=true
ENABLE_API_DOCS=false
ENABLE_SWAGGER_UI=false
```

### 14. Optional: Monitoring (if using)

```
ENABLE_SENTRY=false
SENTRY_DSN=https://your-project-key@sentry.io/your-project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
```

### 15. Optional: Payment Processing (if using Stripe)

```
STRIPE_API_KEY=sk_live_your_stripe_api_key
STRIPE_WEBHOOK_SECRET=whsec_your_stripe_webhook_secret
```

## How to Add These Variables in Railway

1. Go to your Railway project dashboard
2. Click on your service (app)
3. Navigate to the "Variables" tab
4. Click "Add Variable" or "Raw Editor"
5. If using Raw Editor, paste all variables at once
6. If adding individually, add each key-value pair

## Important Notes on Database URLs

### PostgreSQL Connection String Format:
```
postgresql://[user]:[password]@[host]:[port]/[database]
```

For Railway PostgreSQL:
- User: `postgres`
- Host: `postgres.railway.internal` (internal) or the public host if needed
- Port: `5432`
- Database: `railway`

### Redis Connection String Format:
```
redis://[user]:[password]@[host]:[port]/[database_number]
```

For Railway Redis:
- User: `default`
- Host: `redis.railway.internal` (internal) or the public host if needed
- Port: `6379`
- Database: `0` (default)

## Post-Setup Verification

After setting up all environment variables, verify the configuration:

1. Check Railway logs for any connection errors
2. Test database connectivity
3. Verify Shopify OAuth flow works
4. Check Redis connection for caching

## Security Best Practices

1. Never commit these values to Git
2. Use Railway's built-in secret management
3. Rotate keys periodically
4. Use strong, unique passwords for databases
5. Enable two-factor authentication on Railway account
