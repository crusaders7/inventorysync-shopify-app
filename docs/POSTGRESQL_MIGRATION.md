# PostgreSQL Migration Guide

## Overview
This guide walks through migrating from SQLite to PostgreSQL for production deployment.

## Prerequisites

### 1. Install PostgreSQL
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Create Database and User
```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL prompt:
CREATE DATABASE inventorysync_prod;
CREATE USER inventorysync WITH ENCRYPTED PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE inventorysync_prod TO inventorysync;
\q
```

### 3. Update Python Dependencies
```bash
cd /home/brend/inventorysync-shopify-app/backend
source ../venv/bin/activate
pip install psycopg2-binary asyncpg
```

## Migration Steps

### Step 1: Export Data from SQLite
We'll create a script to export all data from SQLite.

### Step 2: Update Configuration
Update the `.env` file:
```env
# Change from:
DATABASE_URL=sqlite:///./inventorysync_dev.db

# To:
DATABASE_URL=postgresql://inventorysync:your_secure_password@localhost:5432/inventorysync_prod
```

### Step 3: Run Migrations
Use Alembic to migrate the schema.

### Step 4: Import Data
Import the exported data into PostgreSQL.

## Database Schema Differences

SQLite vs PostgreSQL differences to handle:
1. **AUTOINCREMENT** → **SERIAL/BIGSERIAL**
2. **BOOLEAN** → PostgreSQL has native boolean
3. **JSON** → PostgreSQL has native JSONB
4. **Timestamp handling** → Better in PostgreSQL

## Performance Optimizations

### 1. Connection Pooling
```python
# Already configured in database.py with async support
```

### 2. Indexes
```sql
-- Add indexes for common queries
CREATE INDEX idx_stores_shop_domain ON stores(shop_domain);
CREATE INDEX idx_products_store_id ON products(store_id);
CREATE INDEX idx_inventory_items_variant_id ON inventory_items(variant_id);
CREATE INDEX idx_alerts_store_id_created_at ON alerts(store_id, created_at DESC);
```

### 3. JSONB Indexes for Custom Fields
```sql
-- Index JSONB columns for custom fields
CREATE INDEX idx_products_custom_data ON products USING GIN (custom_data);
CREATE INDEX idx_inventory_custom_data ON inventory_items USING GIN (custom_data);
```

## Backup and Recovery

### Daily Backups
```bash
# Add to crontab
0 2 * * * pg_dump -U inventorysync inventorysync_prod > /backups/inventorysync_$(date +\%Y\%m\%d).sql
```

### Point-in-Time Recovery
Enable WAL archiving for PITR capability.

## Monitoring

### 1. Connection Monitoring
```sql
-- Check active connections
SELECT pid, usename, application_name, client_addr, state 
FROM pg_stat_activity 
WHERE datname = 'inventorysync_prod';
```

### 2. Slow Query Log
```sql
-- Enable slow query logging
ALTER SYSTEM SET log_min_duration_statement = 1000; -- Log queries over 1 second
```

## Production Checklist

- [ ] PostgreSQL installed and configured
- [ ] Database and user created
- [ ] Python dependencies installed
- [ ] Data migrated successfully
- [ ] Indexes created
- [ ] Backup strategy implemented
- [ ] Monitoring configured
- [ ] Connection pooling tested
- [ ] Performance benchmarked
