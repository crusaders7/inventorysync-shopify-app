#!/bin/bash

# Set Railway environment variables for production

echo "Setting Railway environment variables..."

# Generated secrets (replace with the ones from generate_secrets.py output)
railway variables set SECRET_KEY='eDI=S^&$|&lhh;=QCf>WA2-I}vH#kKFU9m#bS;KxaX+;Yw;;Z9,DC3=IL]KdDI'
railway variables set JWT_SECRET_KEY="LGgbaLrAk9cRSLXdMSeF_uaBDTjFaBqybOBa_50Y_-o="
railway variables set SHOPIFY_WEBHOOK_SECRET="$(openssl rand -base64 32)"

# Application settings
railway variables set ENVIRONMENT="production"
railway variables set APP_NAME="InventorySync"
railway variables set APP_VERSION="1.0.0"
railway variables set DEBUG="false"

# URLs
railway variables set APP_URL="https://inventorysync.prestigecorp.au"
railway variables set FRONTEND_URL="https://inventorysync.prestigecorp.au"

# Shopify settings
railway variables set SHOPIFY_API_KEY="b9e83419bf510cff0b85cf446b4a7750"
railway variables set SHOPIFY_API_SECRET="d10acb73054b2550818d3e8e5775105d"

# Sentry
railway variables set SENTRY_DSN="https://9d4bb65fdc3051703db90ab619ae5438@o4509479242694656.ingest.de.sentry.io/4509654764879952"
railway variables set SENTRY_ENVIRONMENT="production"
railway variables set ENABLE_SENTRY="true"

# Logging
railway variables set LOG_LEVEL="INFO"
railway variables set LOG_FORMAT="json"

# Security
railway variables set RATE_LIMIT_PER_MINUTE="100"
railway variables set DISABLE_RATE_LIMIT="false"
railway variables set CORS_ORIGINS="https://inventorysync.prestigecorp.au,https://*.myshopify.com"

# Features
railway variables set ENABLE_FORECASTING="true"
railway variables set ENABLE_MULTI_LOCATION="true"
railway variables set ENABLE_API_DOCS="false"
railway variables set ENABLE_SWAGGER_UI="false"

echo "Environment variables set successfully!"
echo "Note: DATABASE_URL and REDIS_URL are automatically provided by Railway"
