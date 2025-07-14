# InventorySync Deployment Guide

## Prerequisites

- Docker and Docker Compose installed
- Domain name configured
- SSL certificates (Let's Encrypt recommended)
- PostgreSQL database (or use Docker)
- Redis cache (or use Docker)
- GitHub account for CI/CD
- Shopify Partner account

## Step 1: Generate Production Secrets

```bash
cd scripts
python generate_secrets.py
```

Save the generated secrets securely. You'll need them for the next steps.

## Step 2: Configure Environment

1. Copy the environment template:
```bash
cp .env.production.template .env.production
```

2. Edit `.env.production` with your actual values:
- Database credentials
- API keys from Shopify Partners Dashboard
- Domain URLs
- SMTP settings

## Step 3: SSL Certificates

### Option A: Let's Encrypt (Recommended)
```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./ssl/
```

### Option B: Self-signed (Development only)
```bash
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/privkey.pem \
  -out ssl/fullchain.pem
```

## Step 4: Deploy with Docker Compose

### Development/Staging
```bash
# Build and start services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Create initial admin user
docker-compose exec backend python scripts/create_admin.py
```

### Production
```bash
# Use production compose file
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Check logs
docker-compose logs -f
```

## Step 5: Configure Shopify App

1. Go to Shopify Partners Dashboard
2. Create new app or update existing
3. Set App URL: `https://your-domain.com`
4. Set Redirect URLs:
   - `https://your-domain.com/auth/callback`
   - `https://your-domain.com/auth/shopify/callback`
5. Configure webhooks:
   - `https://your-domain.com/api/webhooks/app/uninstalled`
   - `https://your-domain.com/api/webhooks/gdpr/customers_data_request`
   - `https://your-domain.com/api/webhooks/gdpr/customers_redact`
   - `https://your-domain.com/api/webhooks/gdpr/shop_redact`

## Step 6: Set up CI/CD

1. Push code to GitHub
2. Go to Settings > Secrets and add:
   - `DEPLOY_KEY`: SSH private key for server
   - `DEPLOY_HOST`: Your server IP/hostname
   - `DEPLOY_USER`: SSH username
   - `PRODUCTION_URL`: Your domain
   - `SLACK_WEBHOOK`: (optional) Slack notifications

3. Enable GitHub Actions
4. Push to `production` branch to deploy

## Step 7: Post-Deployment

1. Test the application:
```bash
# Health check
curl https://your-domain.com/health

# API docs
open https://your-domain.com/docs
```

2. Configure monitoring:
- Set up Sentry for error tracking
- Configure uptime monitoring (e.g., UptimeRobot)
- Set up log aggregation (e.g., Papertrail)

3. Set up backups:
```bash
# Database backup
docker-compose exec postgres pg_dump -U inventorysync inventorysync_prod > backup.sql

# Automated backups (add to crontab)
0 2 * * * /opt/inventorysync/scripts/backup.sh
```

## Step 8: Performance Optimization

1. Enable Redis caching:
```python
# Already configured in the app
# Check Redis is working:
docker-compose exec redis redis-cli ping
```

2. Configure CDN for static assets:
- CloudFlare (recommended)
- AWS CloudFront
- Fastly

3. Enable compression in nginx:
```nginx
gzip on;
gzip_types text/plain application/json application/javascript text/css;
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Restart services
docker-compose restart
```

### Database connection issues
```bash
# Test connection
docker-compose exec backend python -c "from database import engine; print(engine.pool.status())"

# Reset database
docker-compose down -v
docker-compose up -d
```

### SSL issues
```bash
# Check certificate validity
openssl x509 -in ssl/fullchain.pem -text -noout

# Renew Let's Encrypt
sudo certbot renew
```

## Security Checklist

- [ ] Change all default passwords
- [ ] Enable firewall (allow only 80, 443, 22)
- [ ] Disable root SSH login
- [ ] Set up fail2ban
- [ ] Regular security updates
- [ ] Monitor for vulnerabilities
- [ ] Regular secret rotation

## Monitoring URLs

- Health Check: `https://your-domain.com/health`
- Metrics: `https://your-domain.com/metrics`
- API Docs: `https://your-domain.com/docs`
- Admin Panel: `https://your-domain.com/admin` (if enabled)

## Support

For issues:
1. Check logs: `docker-compose logs`
2. Check documentation
3. Open GitHub issue
4. Contact support@your-domain.com
