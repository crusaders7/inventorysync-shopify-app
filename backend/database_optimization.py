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
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_store_id ON products(store_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_shopify_product_id ON products(shopify_product_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_handle ON products(handle);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_vendor ON products(vendor);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_status ON products(status);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_updated_at ON products(updated_at);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_store_status ON products(store_id, status);
    """,
    
    """
    -- Product variants table indexes
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_variants_product_id ON product_variants(product_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_variants_shopify_variant_id ON product_variants(shopify_variant_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_variants_sku ON product_variants(sku);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_variants_barcode ON product_variants(barcode);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_variants_updated_at ON product_variants(updated_at);
    """,
    
    """
    -- Inventory items table indexes
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_items_store_id ON inventory_items(store_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_items_location_id ON inventory_items(location_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_items_variant_id ON inventory_items(variant_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_items_available_quantity ON inventory_items(available_quantity);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_items_reorder_point ON inventory_items(reorder_point);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_items_store_location ON inventory_items(store_id, location_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_items_variant_location ON inventory_items(variant_id, location_id);
    """,
    
    """
    -- Alerts table indexes
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_store_id ON alerts(store_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_alert_type ON alerts(alert_type);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_severity ON alerts(severity);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_is_resolved ON alerts(is_resolved);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_store_type ON alerts(store_id, alert_type);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_active ON alerts(store_id, is_resolved) WHERE is_resolved = false;
    """,
    
    """
    -- Workflow rules table indexes
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workflow_rules_store_id ON workflow_rules(store_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workflow_rules_trigger_event ON workflow_rules(trigger_event);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workflow_rules_is_active ON workflow_rules(is_active);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workflow_rules_priority ON workflow_rules(priority);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workflow_rules_last_executed_at ON workflow_rules(last_executed_at);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workflow_rules_store_active ON workflow_rules(store_id, is_active) WHERE is_active = true;
    """,
    
    """
    -- Custom field definitions indexes
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_custom_field_defs_store_id ON custom_field_definitions(store_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_custom_field_defs_field_type ON custom_field_definitions(field_type);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_custom_field_defs_target_entity ON custom_field_definitions(target_entity);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_custom_field_defs_is_active ON custom_field_definitions(is_active);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_custom_field_defs_store_entity ON custom_field_definitions(store_id, target_entity);
    """,
    
    """
    -- Inventory movements indexes
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_movements_inventory_item_id ON inventory_movements(inventory_item_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_movements_movement_type ON inventory_movements(movement_type);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_movements_created_at ON inventory_movements(created_at);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_movements_item_date ON inventory_movements(inventory_item_id, created_at DESC);
    """,
    
    """
    -- Stores table indexes
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_stores_shopify_domain ON stores(shopify_domain);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_stores_subscription_status ON stores(subscription_status);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_stores_is_active ON stores(is_active);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_stores_created_at ON stores(created_at);
    """,
    
    """
    -- Locations table indexes
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_locations_store_id ON locations(store_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_locations_shopify_location_id ON locations(shopify_location_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_locations_is_active ON locations(is_active);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_locations_store_active ON locations(store_id, is_active) WHERE is_active = true;
    """,
    
    """
    -- JSONB indexes for custom data
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_custom_data_gin ON products USING gin(custom_data);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_variants_custom_data_gin ON product_variants USING gin(custom_data);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_custom_data_gin ON inventory_items USING gin(custom_data);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_custom_data_gin ON alerts USING gin(custom_data);
    """,
    
    """
    -- Partial indexes for common queries
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_low_stock ON inventory_items(store_id, variant_id) WHERE available_quantity < reorder_point;
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_out_of_stock ON inventory_items(store_id, variant_id) WHERE available_quantity = 0;
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_active ON products(store_id, updated_at) WHERE status = 'active';
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workflow_rules_active ON workflow_rules(store_id, trigger_event) WHERE is_active = true;
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
    "ANALYZE stores;",
    "ANALYZE products;",
    "ANALYZE product_variants;",
    "ANALYZE inventory_items;",
    "ANALYZE locations;",
    "ANALYZE alerts;",
    "ANALYZE workflow_rules;",
    "ANALYZE custom_field_definitions;",
    "ANALYZE inventory_movements;"
]

async def run_optimization():
    """Run database optimization"""
    from sqlalchemy.ext.asyncio import create_async_engine
    from config import get_database_url
    
    # Create async engine
    DATABASE_URL = get_database_url()
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    
    async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
    
    async with async_engine.begin() as conn:
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
    
    await async_engine.dispose()

async def create_materialized_views():
    """Create materialized views for reporting"""
    from sqlalchemy.ext.asyncio import create_async_engine
    from config import get_database_url
    
    # Create async engine
    DATABASE_URL = get_database_url()
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    
    async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
    
    views = [
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_inventory_summary AS
        SELECT 
            p.store_id,
            p.id as product_id,
            p.title,
            p.vendor,
            v.id as variant_id,
            v.sku,
            v.title as variant_title,
            SUM(i.available_quantity) as total_quantity,
            SUM(i.available_quantity * v.cost_per_item) as total_value,
            COUNT(DISTINCT i.location_id) as location_count,
            MIN(i.available_quantity) as min_location_quantity,
            MAX(i.available_quantity) as max_location_quantity,
            p.updated_at
        FROM products p
        JOIN product_variants v ON p.id = v.product_id
        LEFT JOIN inventory_items i ON v.id = i.variant_id
        GROUP BY p.store_id, p.id, p.title, p.vendor, v.id, v.sku, v.title, p.updated_at;
        
        CREATE UNIQUE INDEX ON mv_inventory_summary(variant_id);
        CREATE INDEX ON mv_inventory_summary(store_id);
        CREATE INDEX ON mv_inventory_summary(product_id);
        CREATE INDEX ON mv_inventory_summary(sku);
        """,
        
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_alert_summary AS
        SELECT 
            store_id,
            alert_type,
            severity,
            is_resolved,
            COUNT(*) as alert_count,
            MIN(created_at) as oldest_alert,
            MAX(created_at) as newest_alert
        FROM alerts
        GROUP BY store_id, alert_type, severity, is_resolved;
        
        CREATE INDEX ON mv_alert_summary(store_id);
        CREATE INDEX ON mv_alert_summary(alert_type);
        CREATE INDEX ON mv_alert_summary(is_resolved);
        """,
        
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_movements AS
        SELECT 
            i.store_id,
            i.variant_id,
            v.product_id,
            DATE(m.created_at) as movement_date,
            m.movement_type,
            SUM(m.quantity_change) as total_change,
            COUNT(*) as movement_count
        FROM inventory_movements m
        JOIN inventory_items i ON m.inventory_item_id = i.id
        JOIN product_variants v ON i.variant_id = v.id
        GROUP BY i.store_id, i.variant_id, v.product_id, DATE(m.created_at), m.movement_type;
        
        CREATE INDEX ON mv_daily_movements(store_id, movement_date);
        CREATE INDEX ON mv_daily_movements(variant_id, movement_date);
        CREATE INDEX ON mv_daily_movements(product_id, movement_date);
        """
    ]
    
    async with async_engine.begin() as conn:
        logger.info("Creating materialized views...")
        for view in views:
            try:
                await conn.execute(text(view))
                logger.info("Created materialized view")
            except Exception as e:
                logger.warning(f"Materialized view warning: {e}")
    
    await async_engine.dispose()

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
