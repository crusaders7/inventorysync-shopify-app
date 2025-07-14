# InventorySync Deployment Guide

## Production Server Requirements

- **Server**: Ubuntu 22.04 LTS or later
- **Database**: PostgreSQL 15+
- **Cache**: Redis 7+
- **Hardware**:
  - Minimum: 2 CPU cores, 4GB RAM, 20GB SSD
  - Recommended: 4 CPU cores, 8GB RAM, 50GB SSD
- **Network**: Static IP, ports 80/443 open

## Step-by-Step Deployment Instructions

### Prerequisites

1. Install Docker, Docker Compose
2. Deploy from GitHub with CI/CD setup

### Deploy with Docker Compose

1. **Build and start services**:
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

2. **Run database migrations**:
   ```bash
   docker exec inventorysync-backend alembic upgrade head
   ```

3. **Verify all services are running**:
   ```bash
   docker ps
   ```

## Environment Variable Configuration

1. Copy the template env file:
   ```bash
   cp .env.production.template .env.production
   ```
   
2. Add actual values for:
   - Database credentials
   - API keys from Shopify Partners Dashboard
   - Domain URLs

## Database Migration Procedures

1. Run migrations to apply database structure updates:
   ```bash
   docker exec inventorysync-backend alembic upgrade head
   ```

2. Optimize database:
   ```bash
   docker exec inventorysync-backend python backend/scripts/optimize_database.py
   ```

## SSL Certificate Setup

### Using Let's Encrypt

1. Install certbot:
   ```bash
   sudo apt-get install certbot
   ```

2. Generate certificates:
   ```bash
   certbot certonly --standalone -d your-domain.com
   ```

3. Auto-renewal setup:
   ```bash
   crontab -e
   0 0 * * * certbot renew --quiet
   ```

## Monitoring and Logging Setup

### Logging

- Configured via `backend/config/logging.yaml`
- Use rotating file handlers for logs (`logs/inventorysync.log`)

### Monitoring

1. PostgreSQL performance monitoring script:
   ```bash
   python backend/scripts/monitor_postgresql.py
   ```
   
2. Set up Grafana + Prometheus (defined in `docker-compose`):
   ```yaml
   services:
     prometheus:
       image: prom/prometheus:latest
       ...

     grafana:
       image: grafana/grafana:latest
       ...
   ```

## Rollback Procedures

1. **Database Backup** (before deployment):
   ```bash
   docker exec inventorysync-postgres pg_dump -U postgres inventorysync_prod > backup_pre_deploy.sql
   ```

2. **Quick Rollback** to previous state:
   ```bash
   docker-compose -f docker-compose.prod.yml down
   docker tag inventorysync-backend:previous inventorysync-backend:latest
   docker-compose -f docker-compose.prod.yml up -d
   ```

