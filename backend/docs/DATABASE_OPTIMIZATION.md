# Database Optimization Guide

This document outlines the comprehensive database optimization strategy for InventorySync, ensuring excellent performance as the application scales.

## Overview

Our database optimization strategy focuses on:
- **Query Performance**: Fast response times for all user operations
- **Scalability**: Efficient handling of large datasets and high concurrent usage
- **Index Strategy**: Comprehensive indexing for common query patterns
- **Monitoring**: Continuous performance monitoring and analysis

## Index Strategy

### Primary Indexes

#### 1. Foreign Key Indexes
All foreign key relationships are indexed to ensure fast JOINs:
```sql
-- Store relationships
CREATE INDEX idx_products_store_id ON products(store_id);
CREATE INDEX idx_inventory_store_id ON inventory_items(store_id);
CREATE INDEX idx_alerts_store_id ON alerts(store_id);

-- Product relationships  
CREATE INDEX idx_variants_product_id ON product_variants(product_id);
CREATE INDEX idx_inventory_variant_id ON inventory_items(variant_id);
```

#### 2. Business Logic Indexes
Critical for application functionality:
```sql
-- SKU lookups (extremely frequent)
CREATE INDEX idx_variants_sku ON product_variants(sku);

-- Low stock detection
CREATE INDEX idx_inventory_low_stock ON inventory_items(store_id, available_quantity, reorder_point);

-- Alert management
CREATE INDEX idx_alerts_store_unresolved ON alerts(store_id, is_resolved, created_at);
```

#### 3. Composite Indexes
Optimized for multi-column queries:
```sql
-- Product filtering and search
CREATE INDEX idx_products_store_status ON products(store_id, status);
CREATE INDEX idx_products_store_type ON products(store_id, product_type);

-- Inventory management
CREATE INDEX idx_inventory_store_location ON inventory_items(store_id, location_id);
CREATE INDEX idx_inventory_variant_location ON inventory_items(variant_id, location_id);
```

#### 4. JSONB Indexes (PostgreSQL)
For custom field searches:
```sql
-- GIN indexes for JSONB custom_data fields
CREATE INDEX idx_products_custom_data_gin ON products USING GIN (custom_data);
CREATE INDEX idx_variants_custom_data_gin ON product_variants USING GIN (custom_data);
CREATE INDEX idx_inventory_custom_data_gin ON inventory_items USING GIN (custom_data);
```

### Index Management

#### Creating Indexes
Use the provided Alembic migration:
```bash
# Apply the comprehensive index migration
alembic upgrade head
```

#### Manual Index Creation
```bash
# Use the optimization CLI tool
python scripts/optimize_database.py suggest-indexes --apply
```

## Query Optimization Patterns

### 1. Store-Scoped Queries
Always include `store_id` in WHERE clauses for multi-tenant queries:
```sql
-- Good: Uses store index
SELECT * FROM products WHERE store_id = 1 AND status = 'active';

-- Bad: Table scan without store_id
SELECT * FROM products WHERE status = 'active';
```

### 2. Pagination
Always use LIMIT/OFFSET for paginated queries:
```sql
-- Good: Limited result set
SELECT * FROM products WHERE store_id = 1 ORDER BY created_at DESC LIMIT 50 OFFSET 0;

-- Bad: Returns all results
SELECT * FROM products WHERE store_id = 1 ORDER BY created_at DESC;
```

### 3. JOIN Optimization
Use appropriate JOIN types and ensure indexes exist:
```sql
-- Optimized inventory query with proper indexes
SELECT p.title, v.sku, i.available_quantity
FROM products p
JOIN product_variants v ON p.id = v.product_id
JOIN inventory_items i ON v.id = i.variant_id
WHERE p.store_id = 1 AND i.available_quantity <= i.reorder_point;
```

### 4. Custom Field Queries
Use JSONB operators efficiently (PostgreSQL):
```sql
-- Efficient JSONB query with GIN index
SELECT * FROM products 
WHERE store_id = 1 AND custom_data @> '{"category": "Electronics"}';

-- Less efficient nested key access
SELECT * FROM products 
WHERE store_id = 1 AND custom_data->>'category' = 'Electronics';
```

## Performance Monitoring

### Using the Database Optimizer

#### 1. Run Performance Analysis
```bash
# Generate comprehensive performance report
python scripts/optimize_database.py analyze --output performance_report.json
```

#### 2. Check for Missing Indexes
```bash
# Analyze and suggest missing indexes
python scripts/optimize_database.py suggest-indexes

# Apply suggested indexes automatically
python scripts/optimize_database.py suggest-indexes --apply
```

#### 3. Profile Specific Queries
```bash
# Profile a slow query
python scripts/optimize_database.py profile-query \
  --query "SELECT * FROM products WHERE store_id = :store_id AND title ILIKE '%:search%'" \
  --params '{"store_id": 1, "search": "iPhone"}' \
  --iterations 10
```

#### 4. Check Index Usage
```bash
# Identify unused indexes
python scripts/optimize_database.py check-indexes --show-sizes
```

### Performance Metrics

#### Response Time Targets
- Simple queries (single table): < 10ms
- Complex queries (3+ JOINs): < 100ms
- Reports and analytics: < 2s
- Bulk operations: < 30s

#### Scalability Targets
- 100,000+ products per store
- 1,000+ concurrent users
- 10,000+ inventory transactions per day
- Sub-second response times for 95% of queries

## Database Maintenance

### Regular Maintenance Tasks

#### 1. Index Maintenance
```sql
-- PostgreSQL: Rebuild indexes if needed
REINDEX INDEX CONCURRENTLY idx_products_store_status;

-- Check for bloated indexes
SELECT schemaname, tablename, indexname, 
       pg_size_pretty(pg_relation_size(indexname::regclass)) as size
FROM pg_indexes WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexname::regclass) DESC;
```

#### 2. Statistics Updates
```sql
-- Update table statistics for query planner
ANALYZE products;
ANALYZE inventory_items;
ANALYZE alerts;
```

#### 3. Cleanup Unused Indexes
```bash
# Identify and remove unused indexes
python scripts/optimize_database.py check-indexes
```

### Monitoring Queries

#### 1. Slow Query Detection
```sql
-- PostgreSQL: Enable slow query logging
ALTER SYSTEM SET log_min_duration_statement = 1000; -- Log queries > 1s
SELECT pg_reload_conf();
```

#### 2. Index Usage Monitoring
```sql
-- Check index usage statistics
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
WHERE idx_scan = 0  -- Unused indexes
ORDER BY pg_relation_size(indexname::regclass) DESC;
```

## Advanced Optimization Techniques

### 1. Partitioning (Future Enhancement)
For very large datasets, consider table partitioning:
```sql
-- Example: Partition alerts by month
CREATE TABLE alerts_2024_01 PARTITION OF alerts
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### 2. Materialized Views
For complex analytics queries:
```sql
-- Example: Pre-computed inventory summary
CREATE MATERIALIZED VIEW inventory_summary AS
SELECT 
    p.store_id,
    p.product_type,
    COUNT(*) as product_count,
    SUM(i.available_quantity) as total_stock,
    AVG(i.available_quantity) as avg_stock
FROM products p
JOIN product_variants v ON p.id = v.product_id
JOIN inventory_items i ON v.id = i.variant_id
GROUP BY p.store_id, p.product_type;

-- Refresh periodically
REFRESH MATERIALIZED VIEW CONCURRENTLY inventory_summary;
```

### 3. Connection Pooling
Configure appropriate connection pooling:
```python
# SQLAlchemy connection pool settings
engine = create_engine(
    DATABASE_URL,
    pool_size=20,          # Base number of connections
    max_overflow=30,       # Additional connections when needed
    pool_pre_ping=True,    # Validate connections
    pool_recycle=3600      # Recycle connections every hour
)
```

## Database-Specific Optimizations

### PostgreSQL
- Use JSONB for custom fields (indexed with GIN)
- Enable query planning optimizations
- Configure appropriate work_mem and shared_buffers
- Use EXPLAIN ANALYZE for query optimization

### SQLite (Development)
- Enable WAL mode for better concurrency
- Use appropriate journal mode
- Regular VACUUM and ANALYZE operations

## Performance Testing

### Load Testing Queries
```python
# Example performance test
def test_product_search_performance():
    start_time = time.time()
    
    products = session.query(Product).filter(
        Product.store_id == 1,
        Product.title.ilike('%iPhone%')
    ).limit(50).all()
    
    execution_time = time.time() - start_time
    assert execution_time < 0.1  # Should complete in < 100ms
```

### Continuous Monitoring
Integrate performance monitoring into CI/CD:
```bash
# Run performance tests
python scripts/optimize_database.py analyze
```

## Troubleshooting

### Common Performance Issues

#### 1. Missing Indexes
**Symptom**: Slow queries, high CPU usage
**Solution**: Run index analysis and apply suggestions
```bash
python scripts/optimize_database.py suggest-indexes --apply
```

#### 2. Large Result Sets
**Symptom**: Memory issues, slow responses
**Solution**: Implement proper pagination
```python
# Good: Paginated query
query = session.query(Product).filter(Product.store_id == store_id)
page = query.offset(offset).limit(limit).all()
```

#### 3. N+1 Query Problems
**Symptom**: Multiple queries for related data
**Solution**: Use proper eager loading
```python
# Good: Single query with joins
products = session.query(Product).options(
    joinedload(Product.variants).joinedload(ProductVariant.inventory_items)
).filter(Product.store_id == store_id).all()
```

#### 4. Inefficient JSONB Queries
**Symptom**: Slow custom field searches
**Solution**: Use proper JSONB operators and indexes
```sql
-- Good: Uses GIN index
WHERE custom_data @> '{"category": "Electronics"}'

-- Bad: Cannot use index efficiently  
WHERE custom_data->>'category' = 'Electronics'
```

## Best Practices

### 1. Query Design
- Always include store_id in multi-tenant queries
- Use appropriate indexes for WHERE, ORDER BY, and JOIN clauses
- Limit result sets with LIMIT clauses
- Use EXISTS instead of IN for large subqueries

### 2. Index Management
- Monitor index usage regularly
- Remove unused indexes to save space
- Create composite indexes for multi-column queries
- Use partial indexes for filtered queries

### 3. Application Design
- Implement proper connection pooling
- Use query builders to prevent SQL injection
- Cache frequent queries when appropriate
- Implement proper error handling for database operations

### 4. Development Workflow
- Run performance analysis before deployment
- Include database migrations in version control
- Test with realistic data volumes
- Monitor performance in production

## Future Enhancements

### Planned Optimizations
1. **Read Replicas**: For scaling read operations
2. **Caching Layer**: Redis for frequently accessed data
3. **Search Engine**: Elasticsearch for full-text search
4. **Analytics Database**: Separate OLAP system for reporting
5. **Automated Optimization**: ML-driven query optimization

### Monitoring Integration
- Integrate with application monitoring (Datadog, New Relic)
- Set up alerting for slow queries
- Dashboard for database performance metrics
- Automated index suggestions based on query patterns

---

For questions or issues with database performance, contact the development team or create an issue in the project repository.