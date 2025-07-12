# Production Deployment Guide for InventorySync

This guide covers the complete process of deploying InventorySync to production.

## Table of Contents
1. [Pre-deployment Checklist](#pre-deployment-checklist)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Database Configuration](#database-configuration)
4. [Environment Variables](#environment-variables)
5. [Security Hardening](#security-hardening)
6. [Deployment Process](#deployment-process)
7. [Post-deployment Verification](#post-deployment-verification)
8. [Monitoring & Maintenance](#monitoring-maintenance)

## Pre-deployment Checklist

### Code Readiness
- [ ] All tests passing
- [ ] No console.log statements in production code
- [ ] Error handling implemented for all API endpoints
- [ ] Input validation on all user inputs
- [ ] Rate limiting configured appropriately
- [ ] CORS settings configured for production domain

### Database
- [ ] PostgreSQL installed and configured
- [ ] Database backups automated
- [ ] Database monitoring in place
- [ ] Indexes created for performance
- [ ] Connection pooling configured

### Security
- [ ] Environment variables secured
- [ ] HTTPS/SSL certificates configured
- [ ] Firewall rules configured
- [ ] Database access restricted
- [ ] API keys rotated
- [ ] Shopify webhook verification enabled

## Infrastructure Setup

### Recommended Stack
- **Server**: Ubuntu 22.04 LTS or later
- **Database**: PostgreSQL 14+
- **Cache**: Redis 6+
- **Web Server**: Nginx
- **Process Manager**: PM2 or systemd
- **SSL**: Let's Encrypt

### Server Requirements
- **Minimum**: 2 CPU cores, 4GB RAM, 20GB SSD
- **Recommended**: 4 CPU cores, 8GB RAM, 50GB SSD
- **Network**: Static IP, ports 80/443 open

## Database Configuration

### PostgreSQL Production Settings

```sql
-- Create production database and user
CREATE USER inventorysync_prod WITH PASSWORD 'use_a_very_strong_password';
CREATE DATABASE inventorysync_prod OWNER inventorysync_prod;
GRANT ALL PRIVILEGES ON DATABASE inventorysync_prod TO inventorysync_prod;

-- Performance tuning (adjust based on server specs)
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET min_wal_size = '1GB';
ALTER SYSTEM SET max_wal_size = '4GB';

-- Reload configuration
SELECT pg_reload_conf();
```

### Connection Pooling

Configure PgBouncer for connection pooling:

```ini
# /etc/pgbouncer/pgbouncer.ini
[databases]
inventorysync_prod = host=localhost port=5432 dbname=inventorysync_prod

[pgbouncer]
listen_port = 6432
listen_addr = localhost
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 100
default_pool_size = 25
```

## Environment Variables

### Production .env Configuration

```bash
# Application Settings
APP_NAME=InventorySync
APP_VERSION=1.0.0
DEBUG=false
ENVIRONMENT=production

# Server Configuration
HOST=0.0.0.0
PORT=8000

# URLs
APP_URL=https://api.yourdomain.com
FRONTEND_URL=https://app.yourdomain.com

# PostgreSQL Database
DATABASE_URL=postgresql://inventorysync_prod:strong_password@localhost:6432/inventorysync_prod
DATABASE_URL_ASYNC=postgresql+asyncpg://inventorysync_prod:strong_password@localhost:6432/inventorysync_prod

# Redis
REDIS_URL=redis://:redis_password@localhost:6379/0

# Shopify App (from Partners Dashboard)
SHOPIFY_API_KEY=your_production_api_key
SHOPIFY_API_SECRET=your_production_api_secret
SHOPIFY_WEBHOOK_SECRET=your_webhook_secret

# Security
SECRET_KEY=generate_256_bit_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Rate Limiting
RATE_LIMIT_PER_MINUTE=300
DISABLE_RATE_LIMIT=false

# CORS
CORS_ORIGINS=https://app.yourdomain.com,https://yourdomain.com

# Monitoring
SENTRY_DSN=your_sentry_dsn
LOG_LEVEL=INFO

# Features
ENABLE_API_DOCS=false
ENABLE_SWAGGER_UI=false
```

## Security Hardening

### 1. Firewall Configuration

```bash
# Allow SSH (change port if using non-standard)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow PostgreSQL only from localhost
sudo ufw allow from 127.0.0.1 to any port 5432

# Enable firewall
sudo ufw enable
```

### 2. Nginx Configuration

```nginx
# /etc/nginx/sites-available/inventorysync
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    
    # SSL Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000" always;
    
    # API rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### 3. Application Security

```python
# Additional security middleware to add to main.py

from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Add to FastAPI app
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["api.yourdomain.com", "*.yourdomain.com"]
)

# Force HTTPS in production
if settings.environment == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
```

## Deployment Process

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.10 python3.10-venv python3-pip
sudo apt install -y postgresql postgresql-contrib
sudo apt install -y redis-server
sudo apt install -y nginx
sudo apt install -y git curl

# Install Node.js for frontend
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install PM2
sudo npm install -g pm2
```

### 2. Application Deployment

```bash
# Create application directory
sudo mkdir -p /var/www/inventorysync
sudo chown $USER:$USER /var/www/inventorysync

# Clone repository
cd /var/www/inventorysync
git clone https://github.com/yourusername/inventorysync-shopify-app.git .

# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy production .env
cp .env.production .env

# Run database migrations
alembic upgrade head

# Frontend setup
cd ../frontend
npm install
npm run build

# Copy built files to nginx directory
sudo cp -r dist/* /var/www/html/
```

### 3. Process Management with PM2

```javascript
// ecosystem.config.js
module.exports = {
  apps: [{
    name: 'inventorysync-api',
    script: '/var/www/inventorysync/backend/venv/bin/python',
    args: '-m uvicorn main:app --host 0.0.0.0 --port 8000',
    cwd: '/var/www/inventorysync/backend',
    env: {
      NODE_ENV: 'production'
    },
    error_file: '/var/log/inventorysync/api-error.log',
    out_file: '/var/log/inventorysync/api-out.log',
    log_file: '/var/log/inventorysync/api-combined.log',
    time: true
  }]
};
```

```bash
# Start application
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup systemd
```

## Post-deployment Verification

### 1. Health Checks

```bash
# Check API health
curl https://api.yourdomain.com/health

# Check database connectivity
curl https://api.yourdomain.com/api/v1/health/database

# Test Shopify webhook
curl -X POST https://api.yourdomain.com/api/v1/webhooks/shopify/test
```

### 2. Performance Tests

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test API performance
ab -n 1000 -c 10 https://api.yourdomain.com/health
```

### 3. Security Scan

```bash
# SSL Test
curl -I https://api.yourdomain.com

# Check security headers
curl -I https://api.yourdomain.com | grep -E "X-Content-Type|X-Frame|Strict-Transport"
```

## Monitoring & Maintenance

### 1. Setup Monitoring Cron Jobs

```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /var/www/inventorysync/backend/scripts/backup_postgresql.py

# Performance monitoring every 5 minutes
*/5 * * * * /var/www/inventorysync/backend/scripts/monitor_postgresql.py

# Log rotation
0 0 * * * /usr/sbin/logrotate /etc/logrotate.d/inventorysync
```

### 2. Log Rotation Configuration

```bash
# /etc/logrotate.d/inventorysync
/var/log/inventorysync/*.log {
    daily
    missingok
    rotate 14
    compress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        pm2 reloadLogs
    endscript
}
```

### 3. Monitoring Dashboard

Set up Grafana + Prometheus for visual monitoring:

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  prometheus_data:
  grafana_data:
```

## Maintenance Tasks

### Weekly
- [ ] Review error logs
- [ ] Check disk usage
- [ ] Verify backups are running
- [ ] Review performance metrics

### Monthly
- [ ] Update dependencies
- [ ] Review security patches
- [ ] Optimize database (VACUUM, ANALYZE)
- [ ] Review and rotate API keys

### Quarterly
- [ ] Full security audit
- [ ] Performance optimization review
- [ ] Disaster recovery test
- [ ] Scale planning review

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   ```bash
   # Check memory usage
   free -m
   # Restart services
   pm2 restart all
   ```

2. **Database Connection Errors**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   # Check connections
   sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"
   ```

3. **Slow API Response**
   ```bash
   # Check CPU usage
   top
   # Check slow queries
   python /var/www/inventorysync/backend/scripts/monitor_postgresql.py
   ```

## Support

For production support:
- Documentation: https://docs.inventorysync.com
- Email: support@inventorysync.com
- Emergency: +1-XXX-XXX-XXXX
