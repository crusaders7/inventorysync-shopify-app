# InventorySync Backend

Advanced inventory management system for Shopify stores with enterprise-level features.

## Features

- **Smart Inventory Management**: Real-time stock tracking, automated reorder points, multi-location support
- **Custom Fields System**: Fully customizable product and inventory attributes
- **Workflow Automation**: Rule-based automation for alerts, notifications, and actions
- **Advanced Analytics**: Forecasting, performance monitoring, and detailed reporting
- **Scalable Architecture**: Optimized for high-performance with comprehensive database indexing

## Quick Start

### Prerequisites

- Python 3.10+
- SQLAlchemy compatible database (PostgreSQL recommended for production)
- Redis (optional, for caching)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up database
alembic upgrade head

# Apply performance optimizations
python scripts/optimize_database.py suggest-indexes --apply

# Run the application
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/inventorysync
# or for development:
DATABASE_URL=sqlite:///./inventorysync_dev.db

# Shopify API
SHOPIFY_API_KEY=your_shopify_api_key
SHOPIFY_API_SECRET=your_shopify_api_secret

# Application
SECRET_KEY=your_secret_key
ENVIRONMENT=development  # or production

# Optional: Redis for caching
REDIS_URL=redis://localhost:6379/0

# Optional: Monitoring
MONITORING_ENABLED=true
LOG_LEVEL=INFO
```

## Database Optimization

This project includes comprehensive database optimization features:

### Performance Analysis

```bash
# Run comprehensive performance analysis
python scripts/optimize_database.py analyze --output performance_report.json

# Check for missing indexes
python scripts/optimize_database.py suggest-indexes

# Apply suggested optimizations
python scripts/optimize_database.py suggest-indexes --apply
```

### Query Profiling

```bash
# Profile a specific query
python scripts/optimize_database.py profile-query \
  --query "SELECT * FROM products WHERE store_id = :store_id" \
  --params '{"store_id": 1}' \
  --iterations 10
```

### Index Management

```bash
# Check index usage statistics
python scripts/optimize_database.py check-indexes --show-sizes

# Optimize custom field queries (PostgreSQL)
python scripts/optimize_database.py optimize-custom-fields
```

See [DATABASE_OPTIMIZATION.md](docs/DATABASE_OPTIMIZATION.md) for detailed optimization guide.

## API Documentation

### Interactive Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

#### Store Management
- `GET /api/dashboard/{shop_domain}` - Get store dashboard
- `POST /api/stores` - Create/update store

#### Products & Inventory
- `GET /api/products/{shop_domain}` - List products
- `GET /api/inventory/{shop_domain}` - Get inventory levels
- `POST /api/inventory/{shop_domain}/adjust` - Adjust inventory

#### Custom Fields
- `GET /api/custom-fields/{shop_domain}` - List custom fields
- `POST /api/custom-fields/{shop_domain}` - Create custom field
- `POST /api/custom-fields/{shop_domain}/templates/{template}` - Apply template

#### Alerts & Workflows
- `GET /api/alerts/{shop_domain}` - List alerts
- `POST /api/workflows/{shop_domain}` - Create workflow rule

#### Monitoring
- `GET /api/monitoring/health` - Health check
- `GET /api/monitoring/metrics` - Performance metrics (admin only)

## Architecture

### Database Models

- **Store**: Shopify store configuration and billing
- **Product/ProductVariant**: Product catalog with custom fields
- **InventoryItem**: Multi-location inventory tracking
- **Location**: Warehouse and store locations
- **Alert**: Smart alerting system
- **CustomFieldDefinition**: Dynamic field schemas
- **WorkflowRule**: Automation rules and triggers

### Key Features

#### Custom Fields System
```python
# Define custom fields for any entity
field = CustomFieldDefinition(
    field_name="season",
    display_name="Season",
    field_type="select",
    target_entity="product",
    validation_rules={"options": ["Spring", "Summer", "Fall", "Winter"]}
)
```

#### Workflow Automation
```python
# Create automation rules
rule = WorkflowRule(
    rule_name="Low Stock Alert",
    trigger_event="inventory_low",
    trigger_conditions={
        "field": "available_quantity",
        "operator": "less_than",
        "value": 10
    },
    actions=[
        {"type": "create_alert", "severity": "high"},
        {"type": "send_email", "to": "manager@store.com"}
    ]
)
```

#### JSONB Custom Data (PostgreSQL)
```sql
-- Efficient custom field queries with GIN indexes
SELECT * FROM products 
WHERE custom_data @> '{"season": "Winter", "material": "Cotton"}';
```

## Testing

### Run Tests
```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Performance tests
pytest tests/test_database_optimization.py -m performance

# API tests
pytest tests/api/
```

### Test Coverage
```bash
# Generate coverage report
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

## Development

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

### Performance Monitoring
```bash
# Check application performance
python scripts/optimize_database.py analyze

# Monitor in production
curl http://localhost:8000/api/v1/monitoring/health
```

## Deployment

### Production Checklist

1. **Database Setup**
   ```bash
   # Apply migrations
   alembic upgrade head
   
   # Optimize indexes
   python scripts/optimize_database.py suggest-indexes --apply
   ```

2. **Environment Configuration**
   - Set `ENVIRONMENT=production`
   - Configure PostgreSQL with proper settings
   - Set up Redis for caching
   - Configure monitoring and logging

3. **Performance Optimization**
   - Enable connection pooling
   - Configure appropriate worker processes
   - Set up CDN for static assets
   - Enable database query monitoring

### Docker Deployment
```bash
# Build container
docker build -t inventorysync-backend .

# Run with docker-compose
docker-compose up -d
```

### Monitoring
- Health checks at `/api/v1/monitoring/health`
- Metrics endpoint `/api/v1/monitoring/metrics` (admin only)
- Comprehensive logging with structured JSON format
- Performance analysis tools built-in

## Security

- **Authentication**: Shopify OAuth 2.0
- **Authorization**: Role-based access control
- **Input Validation**: Comprehensive validation with XSS protection
- **Rate Limiting**: Built-in rate limiting for all endpoints
- **SQL Injection Prevention**: Parameterized queries only
- **CORS**: Configurable CORS policies

## Troubleshooting

### Common Issues

1. **Slow Queries**
   ```bash
   python scripts/optimize_database.py analyze
   ```

2. **High Memory Usage**
   - Check for N+1 query problems
   - Implement pagination for large datasets
   - Use connection pooling

3. **Database Connection Issues**
   - Verify DATABASE_URL format
   - Check connection pool settings
   - Monitor connection usage

### Performance Issues
See [DATABASE_OPTIMIZATION.md](docs/DATABASE_OPTIMIZATION.md) for detailed troubleshooting.

### Logs
- Application logs: `logs/app.log`
- Error logs: `logs/error.log`
- Performance logs: `logs/performance.log`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Run performance analysis
6. Submit a pull request

### Development Guidelines
- Follow PEP 8 style guidelines
- Write comprehensive tests
- Document new features
- Run performance analysis before submitting
- Update API documentation

## License

Proprietary - All rights reserved

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation in `/docs`
- Run diagnostic tools: `python scripts/optimize_database.py analyze`