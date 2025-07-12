# InventorySync Deployment Plan

## 📋 Overview

This document outlines the complete deployment plan for InventorySync to Railway, including all necessary steps, configurations, and monitoring setup.

## 🚀 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Railway Platform                         │
├─────────────────────────┬───────────────────┬──────────────────┤
│    Backend Service      │  Frontend Service │ Database Service │
│    (FastAPI + API)      │  (React + Vite)   │   (PostgreSQL)   │
├─────────────────────────┼───────────────────┼──────────────────┤
│    Redis Service        │ Monitoring Stack  │  Sentry Service  │
│    (Caching/Queue)      │ (Grafana/Prom)    │ (Error Tracking) │
└─────────────────────────┴───────────────────┴──────────────────┘
```

## 📝 Pre-Deployment Checklist

### 1. Code Preparation
- [x] Structured logging with request IDs implemented
- [x] Prometheus metrics integrated
- [x] Health check endpoints created
- [x] Environment-specific configurations
- [ ] Remove all hardcoded values
- [ ] Update all API endpoints to use environment variables
- [ ] Ensure all secrets are in environment variables

### 2. Environment Variables to Configure

#### Backend Service
```env
# Application
ENVIRONMENT=production
APP_NAME=InventorySync
APP_VERSION=1.0.0
APP_URL=https://api.inventorysync.app
FRONTEND_URL=https://app.inventorysync.app

# Database
DATABASE_URL=postgresql://${{PGUSER}}:${{PGPASSWORD}}@${{PGHOST}}:${{PGPORT}}/${{PGDATABASE}}

# Redis
REDIS_URL=redis://${{REDISHOST}}:${{REDISPORT}}

# Shopify
SHOPIFY_API_KEY=your_production_api_key
SHOPIFY_API_SECRET=your_production_api_secret
SHOPIFY_WEBHOOK_SECRET=your_webhook_secret

# Security
SECRET_KEY=generate-with-script
JWT_SECRET_KEY=generate-with-script
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Monitoring
SENTRY_DSN=your-sentry-dsn
ENABLE_SENTRY=true
LOG_LEVEL=INFO
LOG_FORMAT=json

# Monitoring Endpoints (for Prometheus scraping)
METRICS_ENABLED=true

# CORS
CORS_ORIGINS=https://app.inventorysync.app,https://*.myshopify.com
```

#### Frontend Service
```env
VITE_API_URL=https://api.inventorysync.app
VITE_APP_URL=https://app.inventorysync.app
VITE_ENVIRONMENT=production
```

## 🚂 Railway Deployment Steps

### Step 1: Create Railway Project
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Create new project
railway init
```

### Step 2: Configure Services

#### Backend Service (railway.json)
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile.backend"
  },
  "deploy": {
    "numReplicas": 2,
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

#### Frontend Service
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile.frontend"
  },
  "deploy": {
    "numReplicas": 2,
    "startCommand": "npm run preview",
    "healthcheckPath": "/",
    "healthcheckTimeout": 30
  }
}
```

### Step 3: Database Setup
```bash
# Railway automatically provisions PostgreSQL
# Connection details available as environment variables:
# PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE

# Run migrations after deployment
railway run alembic upgrade head
```

### Step 4: Redis Setup
```bash
# Add Redis service in Railway dashboard
# Connection URL will be available as REDIS_URL
```

### Step 5: Deploy Services
```bash
# Deploy backend
railway up -d backend

# Deploy frontend
railway up -d frontend

# Check deployment status
railway status
```

## 🔍 Monitoring Setup

### 1. Prometheus Configuration
Create a monitoring service in Railway:

```yaml
# prometheus-railway.yml
scrape_configs:
  - job_name: 'inventorysync-api'
    static_configs:
      - targets: ['backend.railway.internal:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### 2. Grafana Dashboard
- Import the dashboard from `/monitoring/grafana/dashboards/inventorysync.json`
- Configure alerts for critical metrics
- Set up notification channels (email, Slack)

### 3. Sentry Integration
```bash
# Configure in Railway environment
SENTRY_DSN=https://your-key@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_RELEASE=${{RAILWAY_GIT_COMMIT_SHA}}
```

## 📊 Post-Deployment Verification

### 1. Health Checks
```bash
# Check API health
curl https://api.inventorysync.app/health

# Check metrics endpoint
curl https://api.inventorysync.app/metrics

# Check frontend
curl https://app.inventorysync.app
```

### 2. Database Verification
```bash
# Connect to Railway PostgreSQL
railway run psql

# Verify tables
\dt

# Check migrations
SELECT * FROM alembic_version;
```

### 3. Monitoring Verification
- [ ] Prometheus scraping metrics successfully
- [ ] Grafana dashboards showing data
- [ ] Sentry receiving error reports
- [ ] Alerts configured and working

## 🚨 Rollback Plan

### Automated Rollback
Railway automatically maintains previous deployments:
```bash
# List deployments
railway deployments

# Rollback to previous version
railway rollback <deployment-id>
```

### Manual Rollback Steps
1. Identify the issue from monitoring/logs
2. Rollback database migrations if needed:
   ```bash
   railway run alembic downgrade -1
   ```
3. Restore previous deployment
4. Verify system health

## 📈 Performance Optimization

### 1. Enable Caching
```python
# Already configured in backend
REDIS_URL=redis://...
CACHE_TTL=300  # 5 minutes
```

### 2. Database Optimization
- [ ] Create indexes on frequently queried columns
- [ ] Enable connection pooling
- [ ] Configure statement timeout

### 3. CDN Setup (Optional)
- Configure Cloudflare for static assets
- Set cache headers appropriately

## 🔒 Security Checklist

- [ ] All secrets in environment variables
- [ ] HTTPS enforced on all endpoints
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] SQL injection protection verified
- [ ] XSS protection headers set
- [ ] CSRF protection enabled
- [ ] Dependency scanning enabled

## 📋 Post-Deployment Tasks

### 1. Configure Shopify Webhooks
```bash
# Update webhook URLs in Shopify Partner Dashboard
https://api.inventorysync.app/webhooks/shopify
```

### 2. Set Up Backups
```bash
# Configure automatic PostgreSQL backups
railway plugin postgresql-backup
```

### 3. Configure Custom Domain
```bash
# Add custom domains in Railway
railway domain add api.inventorysync.app
railway domain add app.inventorysync.app
```

### 4. Load Testing
```bash
# Run load tests to verify performance
npm run test:load
```

## 📊 Monitoring Dashboard URLs

After deployment, access monitoring at:
- Grafana: https://monitoring.inventorysync.app
- Prometheus: https://metrics.inventorysync.app
- API Health: https://api.inventorysync.app/health/status

## 🚀 Launch Checklist

### Pre-Launch (1 week before)
- [ ] All environment variables configured
- [ ] Database migrations tested
- [ ] Monitoring alerts configured
- [ ] Backup system verified
- [ ] Load testing completed
- [ ] Security scan passed

### Launch Day
- [ ] Deploy to production
- [ ] Verify all health checks
- [ ] Monitor metrics closely
- [ ] Test critical user flows
- [ ] Announce launch

### Post-Launch (24 hours)
- [ ] Review error logs
- [ ] Check performance metrics
- [ ] Address any issues
- [ ] Gather user feedback
- [ ] Plan next iteration

## 📞 Support Contacts

- **On-Call Engineer**: [Your Phone]
- **Railway Support**: support@railway.app
- **Monitoring Alerts**: alerts@inventorysync.app

## 📚 Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Shopify App Requirements](https://shopify.dev/apps/store/requirements)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)

---

**Last Updated**: December 2024
**Version**: 1.0.0
