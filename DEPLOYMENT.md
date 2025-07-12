# InventorySync Deployment Guide

## Prerequisites

- Docker and Docker Compose installed
- PostgreSQL 15+ database
- Redis 7+ cache server
- SSL certificates for HTTPS
- Domain names configured
- Shopify App credentials

## Environment Setup

### 1. Production Environment Variables

Create `.env.production` file:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/inventorysync_prod
REDIS_URL=redis://:password@host:6379/0

# Security
SECRET_KEY=<generate-with-script>
JWT_SECRET_KEY=<generate-with-script>
ENCRYPTION_KEY=<generate-with-script>

# Shopify
SHOPIFY_API_KEY=<your-api-key>
SHOPIFY_API_SECRET=<generate-with-script>
SHOPIFY_SCOPES=read_products,write_products,read_inventory,write_inventory

# Application
APP_ENV=production
APP_DEBUG=false
FRONTEND_URL=https://app.inventorysync.com
BACKEND_URL=https://api.inventorysync.com

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 2. Generate Secrets

```bash
python3 generate_secrets.py > .env.secrets
```

## Docker Deployment

### 1. Build Images

```bash
# Backend
docker build -f backend/Dockerfile.prod -t inventorysync-backend:latest backend/

# Frontend
docker build -t inventorysync-frontend:latest frontend/
```

### 2. Docker Compose Setup

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    image: inventorysync-backend:latest
    restart: always
    env_file:
      - .env.production
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    volumes:
      - ./logs:/app/logs
    networks:
      - inventorysync

  frontend:
    image: inventorysync-frontend:latest
    restart: always
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
    volumes:
      - ./ssl:/etc/nginx/ssl:ro
      - ./nginx/prod.conf:/etc/nginx/nginx.conf:ro
    networks:
      - inventorysync

  postgres:
    image: postgres:15
    restart: always
    environment:
      POSTGRES_DB: inventorysync_prod
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - inventorysync

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - inventorysync

volumes:
  postgres_data:
  redis_data:

networks:
  inventorysync:
    driver: bridge
```

### 3. Deploy

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Database Setup

### 1. Run Migrations

```bash
docker exec inventorysync-backend alembic upgrade head
```

### 2. Create Indexes

```bash
docker exec inventorysync-backend python database_optimization.py
```

### 3. Setup Backups

Create `/etc/cron.d/inventorysync-backup`:

```cron
0 2 * * * root docker exec inventorysync-postgres pg_dump -U postgres inventorysync_prod | gzip > /backups/inventorysync_$(date +\%Y\%m\%d_\%H\%M\%S).sql.gz
```

## SSL/TLS Configuration

### 1. Using Let's Encrypt

```bash
# Install certbot
apt-get install certbot

# Generate certificates
certbot certonly --standalone -d api.inventorysync.com -d app.inventorysync.com

# Auto-renewal
echo "0 0 * * * root certbot renew --quiet" > /etc/cron.d/certbot-renew
```

### 2. Update Nginx Configuration

Add SSL configuration to `nginx/prod.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name app.inventorysync.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # ... rest of configuration
}
```

## Monitoring Setup

### 1. Health Checks

- Backend: `https://api.inventorysync.com/health`
- Frontend: `https://app.inventorysync.com/health`

### 2. Logging

Configure log aggregation:

```bash
# Install Elastic Stack or use cloud service
docker run -d \
  -p 9200:9200 \
  -p 5601:5601 \
  elastic/elasticsearch:8.0.0
```

### 3. Metrics

Setup Prometheus and Grafana:

```yaml
# Add to docker-compose.prod.yml
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
```

## Performance Optimization

### 1. Enable Caching

```bash
# Warm up cache
docker exec inventorysync-backend python warm_cache.py
```

### 2. CDN Configuration

Configure CloudFlare or another CDN:

- Cache static assets
- Enable Brotli compression
- Set up firewall rules

### 3. Database Optimization

```sql
-- Update statistics
ANALYZE;

-- Check slow queries
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;
```

## Security Hardening

### 1. Firewall Rules

```bash
# Allow only necessary ports
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 2. Fail2ban Setup

```bash
apt-get install fail2ban
cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
systemctl enable fail2ban
```

### 3. Regular Updates

```bash
# Create update script
cat > /usr/local/bin/update-inventorysync.sh << 'EOF'
#!/bin/bash
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
docker system prune -f
EOF

chmod +x /usr/local/bin/update-inventorysync.sh
```

## Shopify App Submission

### 1. App Requirements

- [ ] GDPR webhooks implemented
- [ ] Billing API integrated
- [ ] App Bridge 3.x used
- [ ] Polaris design system
- [ ] Performance benchmarks met

### 2. Security Requirements

- [ ] Content Security Policy
- [ ] HTTPS enforced
- [ ] Authentication secure
- [ ] Data encryption
- [ ] Rate limiting

### 3. Submission Checklist

1. Test in development store
2. Run security audit
3. Update app listing
4. Submit for review
5. Monitor feedback

## Rollback Procedure

### 1. Database Backup

```bash
# Before deployment
docker exec inventorysync-postgres pg_dump -U postgres inventorysync_prod > backup_pre_deploy.sql
```

### 2. Quick Rollback

```bash
# Revert to previous version
docker-compose -f docker-compose.prod.yml down
docker tag inventorysync-backend:previous inventorysync-backend:latest
docker tag inventorysync-frontend:previous inventorysync-frontend:latest
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Common Issues

1. **Database connection errors**
   ```bash
   docker logs inventorysync-backend
   docker exec inventorysync-backend python -c "from database import check_database_health; check_database_health()"
   ```

2. **Redis connection issues**
   ```bash
   docker exec inventorysync-redis redis-cli ping
   ```

3. **High memory usage**
   ```bash
   docker stats
   docker-compose -f docker-compose.prod.yml restart backend
   ```

### Support Contacts

- Technical: tech@inventorysync.com
- Emergency: +1-XXX-XXX-XXXX
- Slack: #inventorysync-ops
