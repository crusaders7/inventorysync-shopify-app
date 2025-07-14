"""Add comprehensive database indexes for performance optimization

Revision ID: 001_perf_indexes
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_perf_indexes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add performance-critical database indexes"""
    
    # =============================================================================
    # STORES TABLE INDEXES
    # =============================================================================
    
    # Shop domain lookup (very frequent)
    op.create_index('idx_stores_shop_domain', 'stores', ['shop_domain'])
    
    # Subscription queries for billing
    op.create_index('idx_stores_subscription_status', 'stores', ['subscription_status'])
    op.create_index('idx_stores_trial_ends_at', 'stores', ['trial_ends_at'])
    
    # GDPR compliance queries
    op.create_index('idx_stores_deletion_scheduled', 'stores', ['deletion_scheduled_at'])
    
    
    # =============================================================================
    # PRODUCTS TABLE INDEXES
    # =============================================================================
    
    # Most common product queries
    op.create_index('idx_products_store_status', 'products', ['store_id', 'status'])
    op.create_index('idx_products_store_type', 'products', ['store_id', 'product_type'])
    op.create_index('idx_products_store_vendor', 'products', ['store_id', 'vendor'])
    
    # Product search and filtering
    op.create_index('idx_products_title_search', 'products', ['title'])
    op.create_index('idx_products_handle', 'products', ['handle'])
    op.create_index('idx_products_vendor', 'products', ['vendor'])
    op.create_index('idx_products_product_type', 'products', ['product_type'])
    
    # Price range queries
    op.create_index('idx_products_price', 'products', ['price'])
    op.create_index('idx_products_cost_per_item', 'products', ['cost_per_item'])
    
    # Time-based queries (recently created, updated)
    op.create_index('idx_products_created_at', 'products', ['created_at'])
    op.create_index('idx_products_updated_at', 'products', ['updated_at'])
    
    # Custom fields queries (JSONB indexes for PostgreSQL)
    # Note: These will only work with PostgreSQL, not SQLite
    try:
        # JSONB GIN index for custom_data field searches
        op.execute('CREATE INDEX CONCURRENTLY idx_products_custom_data_gin ON products USING GIN (custom_data)')
    except Exception:
        # Fallback for SQLite or if JSONB not supported
        pass
    
    
    # =============================================================================
    # PRODUCT VARIANTS TABLE INDEXES
    # =============================================================================
    
    # SKU lookups (extremely frequent)
    op.create_index('idx_variants_sku', 'product_variants', ['sku'])
    op.create_index('idx_variants_sku_not_null', 'product_variants', ['sku'], 
                    postgresql_where=sa.text('sku IS NOT NULL'))
    
    # Barcode lookups
    op.create_index('idx_variants_barcode', 'product_variants', ['barcode'])
    
    # Product relationship queries
    op.create_index('idx_variants_product_id', 'product_variants', ['product_id'])
    
    # Inventory tracking queries
    op.create_index('idx_variants_track_inventory', 'product_variants', ['track_inventory'])
    
    # Price queries for variants
    op.create_index('idx_variants_price', 'product_variants', ['price'])
    
    # Custom fields for variants
    try:
        op.execute('CREATE INDEX CONCURRENTLY idx_variants_custom_data_gin ON product_variants USING GIN (custom_data)')
    except Exception:
        pass
    
    
    # =============================================================================
    # INVENTORY ITEMS TABLE INDEXES
    # =============================================================================
    
    # Most critical inventory queries
    op.create_index('idx_inventory_store_location', 'inventory_items', ['store_id', 'location_id'])
    op.create_index('idx_inventory_variant_location', 'inventory_items', ['variant_id', 'location_id'])
    op.create_index('idx_inventory_store_variant', 'inventory_items', ['store_id', 'variant_id'])
    
    # Stock level queries (for low stock alerts, reports)
    op.create_index('idx_inventory_available_qty', 'inventory_items', ['available_quantity'])
    op.create_index('idx_inventory_reorder_point', 'inventory_items', ['reorder_point'])
    
    # Low stock detection (composite index for performance)
    op.create_index('idx_inventory_low_stock', 'inventory_items', 
                    ['store_id', 'available_quantity', 'reorder_point'])
    
    # Overstock detection
    op.create_index('idx_inventory_overstock', 'inventory_items', 
                    ['store_id', 'available_quantity', 'max_stock_level'])
    
    # Reorder management queries
    op.create_index('idx_inventory_reorder_needed', 'inventory_items', 
                    ['reorder_point', 'available_quantity'])
    
    # Lead time analysis
    op.create_index('idx_inventory_lead_time', 'inventory_items', ['lead_time_days'])
    
    # Custom fields for inventory
    try:
        op.execute('CREATE INDEX CONCURRENTLY idx_inventory_custom_data_gin ON inventory_items USING GIN (custom_data)')
    except Exception:
        pass
    
    
    # =============================================================================
    # INVENTORY MOVEMENTS TABLE INDEXES
    # =============================================================================
    
    # Movement tracking and auditing
    op.create_index('idx_movements_inventory_item', 'inventory_movements', ['inventory_item_id'])
    op.create_index('idx_movements_type', 'inventory_movements', ['movement_type'])
    op.create_index('idx_movements_reference', 'inventory_movements', ['reference_id'])
    
    # Time-based movement analysis
    op.create_index('idx_movements_created_at', 'inventory_movements', ['created_at'])
    op.create_index('idx_movements_item_date', 'inventory_movements', 
                    ['inventory_item_id', 'created_at'])
    
    # Cost analysis
    op.create_index('idx_movements_unit_cost', 'inventory_movements', ['unit_cost'])
    
    
    # =============================================================================
    # LOCATIONS TABLE INDEXES
    # =============================================================================
    
    # Location management
    op.create_index('idx_locations_store_id', 'locations', ['store_id'])
    op.create_index('idx_locations_active', 'locations', ['is_active'])
    op.create_index('idx_locations_manages_inventory', 'locations', ['manages_inventory'])
    
    # Geographic queries
    op.create_index('idx_locations_country', 'locations', ['country'])
    op.create_index('idx_locations_city', 'locations', ['city'])
    
    
    # =============================================================================
    # ALERTS TABLE INDEXES
    # =============================================================================
    
    # Alert dashboard queries (most frequent)
    op.create_index('idx_alerts_store_unresolved', 'alerts', 
                    ['store_id', 'is_resolved', 'created_at'])
    op.create_index('idx_alerts_store_unack', 'alerts', 
                    ['store_id', 'is_acknowledged', 'created_at'])
    
    # Alert filtering
    op.create_index('idx_alerts_type', 'alerts', ['alert_type'])
    op.create_index('idx_alerts_severity', 'alerts', ['severity'])
    op.create_index('idx_alerts_source', 'alerts', ['alert_source'])
    
    # Alert type and severity combination
    op.create_index('idx_alerts_type_severity', 'alerts', ['alert_type', 'severity'])
    
    # Entity-based alert queries
    op.create_index('idx_alerts_entity', 'alerts', ['entity_type', 'entity_id'])
    
    # SKU-based alert lookups
    op.create_index('idx_alerts_product_sku', 'alerts', ['product_sku'])
    
    # Auto-resolution queries
    op.create_index('idx_alerts_auto_resolve', 'alerts', ['auto_resolve_at'])
    op.create_index('idx_alerts_auto_resolvable', 'alerts', ['is_auto_resolvable', 'auto_resolve_at'])
    
    # Alert performance monitoring
    op.create_index('idx_alerts_created_at', 'alerts', ['created_at'])
    op.create_index('idx_alerts_resolved_at', 'alerts', ['resolved_at'])
    
    # Custom alert data
    try:
        op.execute('CREATE INDEX CONCURRENTLY idx_alerts_custom_data_gin ON alerts USING GIN (custom_data)')
    except Exception:
        pass
    
    
    # =============================================================================
    # CUSTOM FIELD DEFINITIONS TABLE INDEXES
    # =============================================================================
    
    # Custom field lookups
    op.create_index('idx_custom_fields_store_entity', 'custom_field_definitions', 
                    ['store_id', 'target_entity'])
    op.create_index('idx_custom_fields_store_active', 'custom_field_definitions', 
                    ['store_id', 'is_active'])
    op.create_index('idx_custom_fields_name', 'custom_field_definitions', ['field_name'])
    op.create_index('idx_custom_fields_type', 'custom_field_definitions', ['field_type'])
    
    # Industry template queries
    op.create_index('idx_custom_fields_template', 'custom_field_definitions', ['industry_template'])
    op.create_index('idx_custom_fields_group', 'custom_field_definitions', ['field_group'])
    
    # Field organization
    op.create_index('idx_custom_fields_order', 'custom_field_definitions', ['display_order'])
    op.create_index('idx_custom_fields_searchable', 'custom_field_definitions', ['is_searchable'])
    op.create_index('idx_custom_fields_filterable', 'custom_field_definitions', ['is_filterable'])
    
    
    # =============================================================================
    # WORKFLOW RULES TABLE INDEXES
    # =============================================================================
    
    # Workflow execution queries
    op.create_index('idx_workflow_store_active', 'workflow_rules', ['store_id', 'is_active'])
    op.create_index('idx_workflow_trigger_event', 'workflow_rules', ['trigger_event'])
    op.create_index('idx_workflow_priority', 'workflow_rules', ['priority'])
    
    # Workflow monitoring
    op.create_index('idx_workflow_execution_count', 'workflow_rules', ['execution_count'])
    op.create_index('idx_workflow_last_executed', 'workflow_rules', ['last_executed_at'])
    
    # Rate limiting
    op.create_index('idx_workflow_rate_limit', 'workflow_rules', ['max_executions_per_hour'])
    
    
    # =============================================================================
    # WORKFLOW EXECUTIONS TABLE INDEXES
    # =============================================================================
    
    # Execution monitoring
    op.create_index('idx_workflow_exec_rule', 'workflow_executions', ['rule_id'])
    op.create_index('idx_workflow_exec_status', 'workflow_executions', ['execution_status'])
    op.create_index('idx_workflow_exec_time', 'workflow_executions', ['created_at'])
    
    # Performance analysis
    op.create_index('idx_workflow_exec_performance', 'workflow_executions', 
                    ['rule_id', 'execution_time_ms'])
    
    
    # =============================================================================
    # SUPPLIERS TABLE INDEXES
    # =============================================================================
    
    # Supplier management
    op.create_index('idx_suppliers_store_id', 'suppliers', ['store_id'])
    op.create_index('idx_suppliers_active', 'suppliers', ['is_active'])
    op.create_index('idx_suppliers_name', 'suppliers', ['name'])
    
    # Performance metrics
    op.create_index('idx_suppliers_reliability', 'suppliers', ['reliability_score'])
    op.create_index('idx_suppliers_quality', 'suppliers', ['quality_score'])
    
    # Geographic queries
    op.create_index('idx_suppliers_country', 'suppliers', ['country'])
    
    
    # =============================================================================
    # PURCHASE ORDERS TABLE INDEXES
    # =============================================================================
    
    # PO management
    op.create_index('idx_po_store_id', 'purchase_orders', ['store_id'])
    op.create_index('idx_po_supplier_id', 'purchase_orders', ['supplier_id'])
    op.create_index('idx_po_status', 'purchase_orders', ['status'])
    op.create_index('idx_po_number', 'purchase_orders', ['po_number'])
    
    # Date-based queries
    op.create_index('idx_po_order_date', 'purchase_orders', ['order_date'])
    op.create_index('idx_po_expected_delivery', 'purchase_orders', ['expected_delivery_date'])
    op.create_index('idx_po_actual_delivery', 'purchase_orders', ['actual_delivery_date'])
    
    # Financial queries
    op.create_index('idx_po_total_amount', 'purchase_orders', ['total_amount'])
    
    
    # =============================================================================
    # PURCHASE ORDER LINE ITEMS TABLE INDEXES
    # =============================================================================
    
    # Line item queries
    op.create_index('idx_po_line_items_po', 'purchase_order_line_items', ['purchase_order_id'])
    op.create_index('idx_po_line_items_variant', 'purchase_order_line_items', ['variant_id'])
    
    # Receiving tracking
    op.create_index('idx_po_line_items_received', 'purchase_order_line_items', 
                    ['quantity_ordered', 'quantity_received'])
    
    
    # =============================================================================
    # FORECASTS TABLE INDEXES
    # =============================================================================
    
    # Forecast queries
    op.create_index('idx_forecasts_variant', 'forecasts', ['variant_id'])
    op.create_index('idx_forecasts_location', 'forecasts', ['location_id'])
    op.create_index('idx_forecasts_date', 'forecasts', ['forecast_date'])
    op.create_index('idx_forecasts_period', 'forecasts', ['forecast_period'])
    
    # Forecast analysis
    op.create_index('idx_forecasts_confidence', 'forecasts', ['confidence_level'])
    op.create_index('idx_forecasts_accuracy', 'forecasts', ['accuracy_score'])
    
    
    # =============================================================================
    # ALERT TEMPLATES TABLE INDEXES
    # =============================================================================
    
    # Template management
    op.create_index('idx_alert_templates_store', 'alert_templates', ['store_id'])
    op.create_index('idx_alert_templates_active', 'alert_templates', ['is_active'])
    op.create_index('idx_alert_templates_type', 'alert_templates', ['alert_type'])
    
    # Usage tracking
    op.create_index('idx_alert_templates_usage', 'alert_templates', ['usage_count'])
    op.create_index('idx_alert_templates_last_used', 'alert_templates', ['last_used_at'])


def downgrade():
    """Remove all performance indexes"""
    
    # Drop indexes in reverse order
    index_names = [
        # Alert templates
        'idx_alert_templates_last_used',
        'idx_alert_templates_usage',
        'idx_alert_templates_type',
        'idx_alert_templates_active',
        'idx_alert_templates_store',
        
        # Forecasts
        'idx_forecasts_accuracy',
        'idx_forecasts_confidence',
        'idx_forecasts_period',
        'idx_forecasts_date',
        'idx_forecasts_location',
        'idx_forecasts_variant',
        
        # Purchase order line items
        'idx_po_line_items_received',
        'idx_po_line_items_variant',
        'idx_po_line_items_po',
        
        # Purchase orders
        'idx_po_total_amount',
        'idx_po_actual_delivery',
        'idx_po_expected_delivery',
        'idx_po_order_date',
        'idx_po_number',
        'idx_po_status',
        'idx_po_supplier_id',
        'idx_po_store_id',
        
        # Suppliers
        'idx_suppliers_country',
        'idx_suppliers_quality',
        'idx_suppliers_reliability',
        'idx_suppliers_name',
        'idx_suppliers_active',
        'idx_suppliers_store_id',
        
        # Workflow executions
        'idx_workflow_exec_performance',
        'idx_workflow_exec_time',
        'idx_workflow_exec_status',
        'idx_workflow_exec_rule',
        
        # Workflow rules
        'idx_workflow_rate_limit',
        'idx_workflow_last_executed',
        'idx_workflow_execution_count',
        'idx_workflow_priority',
        'idx_workflow_trigger_event',
        'idx_workflow_store_active',
        
        # Custom field definitions
        'idx_custom_fields_filterable',
        'idx_custom_fields_searchable',
        'idx_custom_fields_order',
        'idx_custom_fields_group',
        'idx_custom_fields_template',
        'idx_custom_fields_type',
        'idx_custom_fields_name',
        'idx_custom_fields_store_active',
        'idx_custom_fields_store_entity',
        
        # Alerts
        'idx_alerts_resolved_at',
        'idx_alerts_created_at',
        'idx_alerts_auto_resolvable',
        'idx_alerts_auto_resolve',
        'idx_alerts_product_sku',
        'idx_alerts_entity',
        'idx_alerts_type_severity',
        'idx_alerts_source',
        'idx_alerts_severity',
        'idx_alerts_type',
        'idx_alerts_store_unack',
        'idx_alerts_store_unresolved',
        
        # Locations
        'idx_locations_city',
        'idx_locations_country',
        'idx_locations_manages_inventory',
        'idx_locations_active',
        'idx_locations_store_id',
        
        # Inventory movements
        'idx_movements_unit_cost',
        'idx_movements_item_date',
        'idx_movements_created_at',
        'idx_movements_reference',
        'idx_movements_type',
        'idx_movements_inventory_item',
        
        # Inventory items
        'idx_inventory_lead_time',
        'idx_inventory_reorder_needed',
        'idx_inventory_overstock',
        'idx_inventory_low_stock',
        'idx_inventory_reorder_point',
        'idx_inventory_available_qty',
        'idx_inventory_store_variant',
        'idx_inventory_variant_location',
        'idx_inventory_store_location',
        
        # Product variants
        'idx_variants_price',
        'idx_variants_track_inventory',
        'idx_variants_product_id',
        'idx_variants_barcode',
        'idx_variants_sku_not_null',
        'idx_variants_sku',
        
        # Products
        'idx_products_updated_at',
        'idx_products_created_at',
        'idx_products_cost_per_item',
        'idx_products_price',
        'idx_products_product_type',
        'idx_products_vendor',
        'idx_products_handle',
        'idx_products_title_search',
        'idx_products_store_vendor',
        'idx_products_store_type',
        'idx_products_store_status',
        
        # Stores
        'idx_stores_deletion_scheduled',
        'idx_stores_trial_ends_at',
        'idx_stores_subscription_status',
        'idx_stores_shop_domain',
    ]
    
    for index_name in index_names:
        try:
            op.drop_index(index_name)
        except Exception:
            # Index might not exist, continue
            pass
    
    # Drop JSONB indexes if they exist
    try:
        op.execute('DROP INDEX IF EXISTS idx_alerts_custom_data_gin')
        op.execute('DROP INDEX IF EXISTS idx_inventory_custom_data_gin')
        op.execute('DROP INDEX IF EXISTS idx_variants_custom_data_gin')
        op.execute('DROP INDEX IF EXISTS idx_products_custom_data_gin')
    except Exception:
        pass