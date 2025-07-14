# InventorySync Configuration Summary

## Environment Configuration Updated

### 1. Database Configuration
- **Database Type**: PostgreSQL (production-ready)
- **Connection String**: `postgresql://inventorysync:changeme@localhost:5432/inventorysync_prod`
- **Previous**: SQLite (development only)

### 2. Shopify Store Configuration
- **Development Store Domain**: `inventorysync-api.myshopify.com`
- **API Key**: `b9e83419bf510cff0b85cf446b4a7750`
- **Webhook Secret**: `TASBPUAUaqOYpAeopWgzxZZgdcSyt8GN` (generated)

### 3. Additional Services Already Configured
- **Redis**: `redis://localhost:6379/0` (for caching and rate limiting)
- **App URL**: `https://inventorysync.prestigecorp.au`
- **CORS Origins**: Configured for local development and production

## Next Steps

### 1. Start PostgreSQL Service
```bash
# Using Docker Compose
docker-compose up -d postgres

# Or manually if PostgreSQL is installed
sudo systemctl start postgresql
```

### 2. Initialize Database
```bash
cd backend
python init_db.py
```

### 3. Register Webhooks
```bash
cd backend
python configure_shopify_webhooks.py
```

### 4. Test the Configuration
```bash
# Start backend
cd backend
python -m uvicorn main:app --reload

# In another terminal, start frontend
cd frontend
npm run dev
```

## Security Notes

1. **Change Default Passwords**: The current PostgreSQL password is `changeme`. Update this before production:
   ```bash
   # Update in .env file
   DATABASE_URL=postgresql://inventorysync:YOUR_SECURE_PASSWORD@localhost:5432/inventorysync_prod
   ```

2. **Webhook Secret**: The webhook secret has been generated and saved. This will be used to verify all incoming webhooks from Shopify.

3. **Environment-Specific Files**:
   - Development: `.env` (current file)
   - Production: Create `.env.production` with production values

## Monitoring and Optional Services

These are already configured but optional:
- **Sentry**: Add `SENTRY_DSN` when ready
- **Email**: Configure SMTP settings for notifications
- **Prometheus**: Set `PROMETHEUS_ENABLED=true` for metrics

## Git Synchronization

To keep your changes synchronized across computers:

1. **Pull latest changes**:
   ```bash
   git pull origin main
   ```

2. **Push your changes**:
   ```bash
   git add .
   git commit -m "feat: Configure PostgreSQL and development store"
   git push origin main
   ```

## Important Files

- Main configuration: `.env`
- PostgreSQL template: `backend/.env.postgresql`
- Docker services: `docker-compose.yml`
- Webhook secret generator: `scripts/generate_webhook_secret.py`
