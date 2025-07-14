# InventorySync Deployment Checklist

## Pre-Deployment Requirements

### 1. Shopify Partner Account Setup ✅ Waiting
- [ ] Shopify Partner account verified
- [ ] App created in Partner Dashboard
- [ ] API credentials obtained:
  - [ ] API Key
  - [ ] API Secret
  - [ ] Webhook Secret

### 2. Infrastructure Setup
- [ ] Choose deployment platform:
  - [ ] Heroku (simplest)
  - [ ] AWS EC2/ECS
  - [ ] DigitalOcean
  - [ ] Railway.app
  - [ ] Render.com
- [ ] Domain name registered and configured
- [ ] SSL certificate obtained (Let's Encrypt recommended)
- [ ] Database provisioned (PostgreSQL recommended)
- [ ] Redis instance provisioned (for caching)

### 3. Environment Configuration
- [ ] Copy `.env.production.example` to `.env.production`
- [ ] Update all placeholder values:
  - [ ] Shopify API credentials
  - [ ] Database URL
  - [ ] Redis URL
  - [ ] Secret keys (generate strong random values)
  - [ ] Domain URLs
  - [ ] SMTP settings (if using email)

### 4. Code Preparation
- [x] Fix custom fields API error handling ✅
- [x] Create deployment files ✅
- [ ] Run final test suite
- [ ] Update version number in `package.json` and Python files
- [ ] Commit all changes to git
- [ ] Tag release version (e.g., v1.0.0)

### 5. Database Setup
- [ ] Run database migrations:
  ```bash
  alembic upgrade head
  ```
- [ ] Create initial admin user
- [ ] Set up database backups

### 6. Deployment Steps

#### For Heroku:
```bash
# Install Heroku CLI
# Login to Heroku
heroku login

# Create app
heroku create inventorysync-shopify-app

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Add Redis
heroku addons:create heroku-redis:hobby-dev

# Set environment variables
heroku config:set SHOPIFY_API_KEY=your_key
heroku config:set SHOPIFY_API_SECRET=your_secret
# ... set all other variables from .env.production

# Deploy
git push heroku main

# Run migrations
heroku run alembic upgrade head

# Check logs
heroku logs --tail
```

#### For Docker/VPS:
```bash
# Build and start services
docker-compose -f docker-compose.production.yml up -d

# Check logs
docker-compose -f docker-compose.production.yml logs -f

# Run migrations
docker-compose -f docker-compose.production.yml exec backend alembic upgrade head
```

### 7. Post-Deployment Testing
- [ ] Test OAuth flow with real Shopify store
- [ ] Install app on development store
- [ ] Test all critical paths:
  - [ ] Product sync
  - [ ] Inventory updates
  - [ ] Custom fields
  - [ ] Webhook processing
  - [ ] Billing (if enabled)
- [ ] Monitor error logs
- [ ] Check performance metrics

### 8. Shopify App Configuration
- [ ] Update App URL in Partner Dashboard
- [ ] Configure allowed redirect URLs
- [ ] Set up webhook endpoints
- [ ] Configure GDPR webhooks
- [ ] Test installation flow

### 9. Monitoring Setup
- [ ] Configure error tracking (Sentry recommended)
- [ ] Set up uptime monitoring
- [ ] Configure log aggregation
- [ ] Set up alerts for critical errors
- [ ] Monitor webhook delivery

### 10. Documentation
- [ ] Update README with production URLs
- [ ] Document deployment process
- [ ] Create runbook for common issues
- [ ] Update API documentation

### 11. App Store Submission
- [ ] Prepare app listing content
- [ ] Create demo video
- [ ] Submit for Shopify review
- [ ] Address any feedback from review

## Quick Deploy Commands

### Heroku Quick Deploy:
```bash
# From project root
cd backend
heroku create inventorysync-app
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create heroku-redis:hobby-dev
heroku config:set $(cat .env.production | grep -v '^#' | xargs)
git push heroku main
heroku run alembic upgrade head
heroku open
```

### Docker Quick Deploy:
```bash
# From project root
cp .env.production.example .env.production
# Edit .env.production with your values
docker-compose -f docker-compose.production.yml up -d
docker-compose -f docker-compose.production.yml exec backend alembic upgrade head
```

## Rollback Plan

If issues arise:

1. **Heroku Rollback:**
   ```bash
   heroku releases
   heroku rollback v[previous-version]
   ```

2. **Docker Rollback:**
   ```bash
   docker-compose -f docker-compose.production.yml down
   git checkout [previous-tag]
   docker-compose -f docker-compose.production.yml up -d
   ```

## Support Contacts

- Shopify Partner Support: partners@shopify.com
- Shopify API Support: https://help.shopify.com/api
- Community Forums: https://community.shopify.com/c/shopify-apis-and-sdks/bd-p/shopify-apis-and-sdks

## Notes

- Always test in a development store first
- Keep API credentials secure and never commit them
- Monitor rate limits during initial deployment
- Have a backup plan for database migrations
