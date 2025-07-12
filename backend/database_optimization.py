#!/usr/bin/env python3
"""Database optimization script for InventorySync"""

import asyncio
from sqlalchemy import text
from database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PostgreSQL optimization queries
OPTIMIZATION_QUERIES = [
    # Indexes for performance
    """
    -- Products table indexes
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_sku ON products(sku);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_shopify_id ON products(shopify_product_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_barcode ON products(barcode);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_vendor ON products(vendor);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_status ON products(status);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_store_id ON products(store_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_updated_at ON products(updated_at);
    """,
    
    """
    -- Inventory table indexes
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_product_id ON inventory(product_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_location_id ON inventory(location_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_quantity ON inventory(available_quantity);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_updated_at ON inventory(last_updated);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_product_location ON inventory(product_id, location_id);
    """,
    
    """
    -- Alerts table indexes
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_product_id ON alerts(product_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_type ON alerts(alert_type);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_status ON alerts(status);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_priority ON alerts(priority);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_resolved_at ON alerts(resolved_at);
    """,
    
    """
    -- Workflows table indexes
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workflows_store_id ON workflows(store_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workflows_enabled ON workflows(enabled);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workflows_trigger_type ON workflows(trigger_type);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workflows_last_run ON workflows(last_run);
    """,
    
    """
    -- Custom fields indexes
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_custom_fields_store_id ON custom_fields(store_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_custom_fields_field_type ON custom_fields(field_type);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_custom_fields_active ON custom_fields(active);
    """,
    
    """
    -- Inventory movements indexes
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_movements_product_id ON inventory_movements(product_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_movements_location_id ON inventory_movements(location_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_movements_movement_type ON inventory_movements(movement_type);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_movements_timestamp ON inventory_movements(timestamp);
    """,
    
    """
    -- Reports indexes
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_store_id ON reports(store_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_type ON reports(report_type);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_created_at ON reports(created_at);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_status ON reports(status);
    """,
    
    """
    -- JSONB indexes for custom data
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_custom_fields_gin ON products USING gin(custom_fields);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_metadata_gin ON inventory USING gin(metadata);
    """,
    
    """
    -- Partial indexes for common queries
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_active ON alerts(store_id, created_at) WHERE status = 'active';
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_low_stock ON inventory(product_id) WHERE available_quantity < 10;
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_active ON products(store_id, updated_at) WHERE status = 'active';
    """
]

# Query optimization settings
PERFORMANCE_SETTINGS = [
    "ALTER SYSTEM SET shared_buffers = '256MB';",
    "ALTER SYSTEM SET effective_cache_size = '1GB';",
    "ALTER SYSTEM SET work_mem = '16MB';",
    "ALTER SYSTEM SET maintenance_work_mem = '64MB';",
    "ALTER SYSTEM SET random_page_cost = 1.1;",
    "ALTER SYSTEM SET effective_io_concurrency = 200;",
    "ALTER SYSTEM SET max_worker_processes = 4;",
    "ALTER SYSTEM SET max_parallel_workers_per_gather = 2;",
    "ALTER SYSTEM SET max_parallel_workers = 4;",
    "ALTER SYSTEM SET checkpoint_completion_target = 0.9;",
    "ALTER SYSTEM SET wal_buffers = '16MB';",
    "ALTER SYSTEM SET default_statistics_target = 100;",
    "ALTER SYSTEM SET max_connections = 200;",
    "ALTER SYSTEM SET autovacuum = on;",
    "ALTER SYSTEM SET autovacuum_max_workers = 4;",
    "ALTER SYSTEM SET autovacuum_naptime = '30s';",
]

# Table statistics update
ANALYZE_QUERIES = [
    "ANALYZE products;",
    "ANALYZE inventory;",
    "ANALYZE alerts;",
    "ANALYZE workflows;",
    "ANALYZE custom_fields;",
    "ANALYZE inventory_movements;",
    "ANALYZE reports;",
    "ANALYZE stores;"
]

async def run_optimization():
    """Run database optimization"""
    async with engine.begin() as conn:
        logger.info("Starting database optimization...")
        
        # Create indexes
        logger.info("Creating indexes...")
        for query in OPTIMIZATION_QUERIES:
            try:
                await conn.execute(text(query))
                logger.info(f"Executed: {query[:50]}...")
            except Exception as e:
                logger.warning(f"Index creation warning (may already exist): {e}")
        
        # Update statistics
        logger.info("Updating table statistics...")
        for query in ANALYZE_QUERIES:
            try:
                await conn.execute(text(query))
                logger.info(f"Analyzed: {query}")
            except Exception as e:
                logger.warning(f"Analyze warning: {e}")
        
        logger.info("Database optimization complete!")

async def create_materialized_views():
    """Create materialized views for reporting"""
    views = [
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_inventory_summary AS
        SELECT 
            p.store_id,
            p.id as product_id,
            p.title,
            p.sku,
            p.vendor,
            SUM(i.available_quantity) as total_quantity,
            SUM(i.available_quantity * p.cost) as total_value,
            COUNT(DISTINCT i.location_id) as location_count,
            MIN(i.available_quantity) as min_location_quantity,
            MAX(i.available_quantity) as max_location_quantity,
            p.updated_at
        FROM products p
        LEFT JOIN inventory i ON p.id = i.product_id
        GROUP BY p.store_id, p.id, p.title, p.sku, p.vendor, p.updated_at;
        
        CREATE UNIQUE INDEX ON mv_inventory_summary(product_id);
        CREATE INDEX ON mv_inventory_summary(store_id);
        CREATE INDEX ON mv_inventory_summary(sku);
        """,
        
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_alert_summary AS
        SELECT 
            store_id,
            alert_type,
            priority,
            status,
            COUNT(*) as alert_count,
            MIN(created_at) as oldest_alert,
            MAX(created_at) as newest_alert
        FROM alerts
        GROUP BY store_id, alert_type, priority, status;
        
        CREATE INDEX ON mv_alert_summary(store_id);
        CREATE INDEX ON mv_alert_summary(alert_type);
        """,
        
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_movements AS
        SELECT 
            store_id,
            product_id,
            DATE(timestamp) as movement_date,
            movement_type,
            SUM(quantity_change) as total_change,
            COUNT(*) as movement_count
        FROM inventory_movements
        GROUP BY store_id, product_id, DATE(timestamp), movement_type;
        
        CREATE INDEX ON mv_daily_movements(store_id, movement_date);
        CREATE INDEX ON mv_daily_movements(product_id, movement_date);
        """
    ]
    
    async with engine.begin() as conn:
        logger.info("Creating materialized views...")
        for view in views:
            try:
                await conn.execute(text(view))
                logger.info("Created materialized view")
            except Exception as e:
                logger.warning(f"Materialized view warning: {e}")

async def setup_partitioning():
    """Setup table partitioning for large tables"""
    partitioning_queries = [
        """
        -- Partition inventory_movements by month
        CREATE TABLE IF NOT EXISTS inventory_movements_partitioned (
            LIKE inventory_movements INCLUDING ALL
        ) PARTITION BY RANGE (timestamp);
        
        -- Create partitions for the last 6 months and next 3 months
        CREATE TABLE IF NOT EXISTS inventory_movements_y2024m01 PARTITION OF inventory_movements_partitioned
            FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
        CREATE TABLE IF NOT EXISTS inventory_movements_y2024m02 PARTITION OF inventory_movements_partitioned
            FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
        -- Add more partitions as needed
        """
    ]
    
    # Note: Full partitioning implementation would require more complex migration

if __name__ == "__main__":
    asyncio.run(run_optimization())
    asyncio.run(create_materialized_views())
