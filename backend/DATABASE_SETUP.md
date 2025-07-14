# InventorySync Database Setup

This document provides comprehensive instructions for setting up and managing the InventorySync database in both development and production environments.

## Overview

InventorySync uses a sophisticated database architecture with:
- **SQLAlchemy ORM** for database operations
- **Alembic** for database migrations
- **Async/await** patterns for optimal performance
- **PostgreSQL** for production deployments
- **SQLite** for development and testing

## Quick Start

### Development Setup

1. **Initialize the database:**
   ```bash
   python database_manager.py --init --seed
   ```

2. **Check database health:**
   ```bash
   python database_manager.py --health
   ```

### Production Setup

1. **Using Docker Compose:**
   ```bash
   docker-compose up -d postgres redis
   docker-compose up api
   ```

2. **Manual setup:**
   ```bash
   # Set environment variables
   export DATABASE_URL="postgresql://user:password@localhost:5432/inventorysync"
   export ENVIRONMENT="production"
   
   # Initialize database
   python database_manager.py --init
   ```

## Database Architecture

### Core Models

#### Store Management
- **Store**: Shopify store information and settings
- **Location**: Physical locations (warehouses, retail stores)

#### Product Catalog
- **Product**: Shopify products
- **ProductVariant**: Product variants (size, color, etc.)

#### Inventory Management
- **InventoryItem**: Stock levels per variant per location
- **InventoryMovement**: Historical inventory changes

#### Smart Alerts
- **Alert**: Automated inventory alerts and notifications

#### Forecasting
- **Forecast**: AI-powered demand predictions

#### Supply Chain (Future)
- **Supplier**: Supplier information
- **PurchaseOrder**: Purchase orders and tracking

### Database Schema Features

- **Automatic timestamps** on all records
- **Soft deletes** for data integrity
- **Foreign key constraints** for referential integrity
- **Indexes** for query optimization
- **JSON fields** for flexible data storage

## Database Management CLI

The `database_manager.py` script provides comprehensive database management:

### Available Commands

```bash
# Initialize database schema
python database_manager.py --init

# Initialize with sample data (development only)
python database_manager.py --init --seed

# Check database health
python database_manager.py --health

# Reset database (development only)
python database_manager.py --reset

# Backup database
python database_manager.py --backup

# Show environment information
python database_manager.py --info
```

### Examples

```bash
# Full development setup
python database_manager.py --init --seed --info

# Production health check
python database_manager.py --health

# Create backup before maintenance
python database_manager.py --backup maintenance_backup.db
```

## Migration Management

### Creating Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new feature"

# Create empty migration
alembic revision -m "Custom migration"
```

### Running Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade abc123

# Downgrade one revision
alembic downgrade -1

# Show migration history
alembic history --verbose
```

## Environment Configuration

### Development (.env)
```env
DATABASE_URL=sqlite:///./inventorysync_dev.db
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
```

### Production (.env)
```env
DATABASE_URL=postgresql://user:password@localhost:5432/inventorysync
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
SENTRY_DSN=https://your-sentry-dsn
```

## Docker Deployment

### Services

The `docker-compose.yml` includes:

- **postgres**: PostgreSQL 15 with health checks
- **redis**: Redis for caching and background tasks
- **api**: InventorySync API service
- **backup**: Automated backup service

### Starting Services

```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d postgres redis

# View logs
docker-compose logs -f api

# Check service health
docker-compose ps
```

### Environment Variables

Set these in a `.env` file:

```env
POSTGRES_PASSWORD=your_secure_password
REDIS_PASSWORD=your_redis_password
```

## Backup and Recovery

### Automatic Backups

The backup service runs daily at 2 AM and:
- Creates compressed SQL dumps
- Retains backups for 30 days
- Sends notifications (if configured)

### Manual Backup

```bash
# Local backup
python database_manager.py --backup

# Docker backup
docker-compose exec postgres pg_dump -U inventorysync_user inventorysync > backup.sql
```

### Recovery

```bash
# Restore from backup
psql -U inventorysync_user -d inventorysync < backup.sql

# Docker restore
docker-compose exec -T postgres psql -U inventorysync_user -d inventorysync < backup.sql
```

## Performance Optimization

### Database Indexes

Key indexes are automatically created for:
- Primary keys and foreign keys
- Shopify IDs for fast lookups
- SKUs for product searches
- Timestamps for date range queries

### Query Optimization

- Use async sessions for all operations
- Implement connection pooling
- Enable query logging in development
- Monitor slow queries in production

### Scaling Considerations

- **Read Replicas**: For high-read workloads
- **Connection Pooling**: PgBouncer for PostgreSQL
- **Caching**: Redis for frequently accessed data
- **Partitioning**: For large historical data

## Monitoring and Health Checks

### Health Check Endpoint

```http
GET /health
```

Returns database health status:
```json
{
  "status": "healthy",
  "service": "inventorysync-api",
  "database": "healthy",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Database Health Checks

The health check verifies:
- Database connectivity
- Table existence
- Sample query execution
- Connection pool status

### Monitoring Metrics

Monitor these key metrics:
- Connection pool utilization
- Query performance
- Lock contention
- Database size growth
- Backup success rates

## Security

### Access Control

- Use dedicated database users
- Implement least-privilege access
- Rotate passwords regularly
- Use SSL/TLS for connections

### Data Protection

- Enable PostgreSQL SSL
- Encrypt backups
- Secure connection strings
- Audit database access

### Compliance

- PII data handling
- Data retention policies
- GDPR compliance features
- Audit logging

## Troubleshooting

### Common Issues

#### Connection Errors
```bash
# Check database status
python database_manager.py --health

# Verify connection settings
echo $DATABASE_URL
```

#### Migration Errors
```bash
# Check migration status
alembic current

# Show pending migrations
alembic heads

# Reset migration (development only)
alembic downgrade base
alembic upgrade head
```

#### Performance Issues
```bash
# Enable query logging
export LOG_LEVEL=DEBUG

# Check connection pool
docker-compose logs postgres
```

### Getting Help

1. Check the logs: `docker-compose logs -f api`
2. Run health check: `python database_manager.py --health`
3. Review configuration: `python database_manager.py --info`
4. Check PostgreSQL logs: `docker-compose logs postgres`

## Development Workflow

### Local Development

1. **Setup:**
   ```bash
   python database_manager.py --init --seed
   ```

2. **Make model changes:**
   - Edit `models.py`
   - Create migration: `alembic revision --autogenerate -m "Description"`
   - Apply migration: `alembic upgrade head`

3. **Test:**
   ```bash
   python database_manager.py --health
   pytest tests/test_database.py
   ```

### Production Deployment

1. **Pre-deployment:**
   ```bash
   python database_manager.py --backup
   ```

2. **Deploy:**
   ```bash
   docker-compose up -d
   ```

3. **Post-deployment:**
   ```bash
   python database_manager.py --health
   ```

## Best Practices

### Development
- Always use migrations for schema changes
- Test migrations on sample data
- Use transactions for data integrity
- Implement proper error handling

### Production
- Regular automated backups
- Monitor database performance
- Use read replicas for scaling
- Implement proper logging

### Security
- Use environment variables for secrets
- Enable SSL connections
- Regular security updates
- Access auditing

This database setup provides a robust, scalable foundation for the InventorySync application with comprehensive tooling for development, deployment, and maintenance.