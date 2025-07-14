# Railway Environment Variables Setup Checklist

## Pre-Setup Requirements

- [ ] Railway account with project created
- [ ] PostgreSQL service added to Railway project
- [ ] Redis service added to Railway project
- [ ] Shopify Partner account with app credentials

## Step 1: Get Database Connection Strings from Railway

1. **PostgreSQL**:
   - [ ] Go to your Railway project
   - [ ] Click on the PostgreSQL service
   - [ ] Go to "Variables" tab
   - [ ] Copy the `DATABASE_URL` provided by Railway
   - [ ] Note: Railway format is usually: `postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/railway`

2. **Redis**:
   - [ ] Click on the Redis service
   - [ ] Go to "Variables" tab
   - [ ] Copy the `REDIS_URL` provided by Railway
   - [ ] Note: Railway format is usually: `redis://default:[PASSWORD]@[HOST]:[PORT]`

## Step 2: Generate Security Keys

Run the key generation script:
```bash
python3 /home/brend/inventorysync-shopify-app/generate_railway_keys.py
```

Save these generated values:
- [ ] SECRET_KEY
- [ ] JWT_SECRET_KEY
- [ ] ENCRYPTION_KEY
- [ ] SHOPIFY_WEBHOOK_SECRET

## Step 3: Get Shopify Credentials

From Shopify Partner Dashboard:
- [ ] SHOPIFY_API_KEY (Client ID)
- [ ] SHOPIFY_API_SECRET (Client Secret)

## Step 4: Add Variables to Railway

1. Go to your app service in Railway (not PostgreSQL/Redis)
2. Click on "Variables" tab
3. Click "Raw Editor" for bulk import

### Core Variables to Add:

```env
# Database (use Railway's provided URLs)
DATABASE_URL=[PostgreSQL URL from Railway]
DATABASE_URL_ASYNC=[Same as above but with postgresql+asyncpg://]
REDIS_URL=[Redis URL from Railway]

# Security (from generated keys)
SECRET_KEY=[Generated SECRET_KEY]
JWT_SECRET_KEY=[Generated JWT_SECRET_KEY]
ENCRYPTION_KEY=[Generated ENCRYPTION_KEY]

# Shopify
SHOPIFY_API_KEY=[Your Shopify API Key]
SHOPIFY_API_SECRET=[Your Shopify API Secret]
SHOPIFY_WEBHOOK_SECRET=[Generated SHOPIFY_WEBHOOK_SECRET]

# URLs
APP_URL=https://reasonable-perfection.up.railway.app
FRONTEND_URL=https://reasonable-perfection.up.railway.app
BACKEND_URL=https://reasonable-perfection.up.railway.app

# Application
APP_NAME=InventorySync
APP_VERSION=1.0.0
APP_ENV=production
DEBUG=false
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000

# CORS
CORS_ORIGINS=["https://reasonable-perfection.up.railway.app", "https://admin.shopify.com"]
ALLOWED_HOSTS=reasonable-perfection.up.railway.app,*.railway.app

# Performance
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
REDIS_MAX_CONNECTIONS=50
WORKERS=4

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# JWT
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Rate Limiting
RATE_LIMIT_PER_MINUTE=120
DISABLE_RATE_LIMIT=false

# Security Settings
SSL_REDIRECT=true
SECURE_COOKIES=true

# Features
ENABLE_FORECASTING=true
ENABLE_MULTI_LOCATION=true
ENABLE_SUPPLIER_INTEGRATION=true
ENABLE_API_DOCS=false
ENABLE_SWAGGER_UI=false
```

## Step 5: Verify Configuration

- [ ] Click "Deploy" to apply environment variables
- [ ] Check deployment logs for any errors
- [ ] Verify app starts successfully

## Step 6: Test Connections

1. **Database Connection**:
   - [ ] Check logs for "Database connected successfully"
   - [ ] No PostgreSQL connection errors

2. **Redis Connection**:
   - [ ] Check logs for Redis connection confirmation
   - [ ] No Redis connection errors

3. **Application Access**:
   - [ ] Visit https://reasonable-perfection.up.railway.app
   - [ ] Verify app loads without errors

## Common Issues and Solutions

### PostgreSQL Connection Issues
- Ensure you're using Railway's internal hostname (`postgres.railway.internal`)
- Check if password contains special characters that need URL encoding
- Verify the database name (usually `railway`)

### Redis Connection Issues
- Redis on Railway uses `default` as username
- Ensure you're using the internal hostname (`redis.railway.internal`)
- Check password formatting

### CORS Issues
- Ensure CORS_ORIGINS includes your Railway app URL
- Add `https://admin.shopify.com` for Shopify embedded apps

### Environment Variable Format Issues
- Arrays should be in JSON format: `["value1", "value2"]`
- Booleans should be lowercase: `true` or `false`
- Don't wrap values in quotes unless they contain spaces

## Post-Setup Tasks

- [ ] Test Shopify OAuth flow
- [ ] Verify webhook endpoints are accessible
- [ ] Check API endpoints are responding
- [ ] Monitor logs for any runtime errors
- [ ] Set up monitoring/alerting if needed
