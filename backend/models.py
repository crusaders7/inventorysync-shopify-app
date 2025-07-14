"""
InventorySync Database Models
SQLAlchemy models for inventory management system
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
import uuid

# Import Base from database module
from database import Base


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)


class Store(Base, TimestampMixin):
    """Shopify store information"""
    __tablename__ = "stores"
    
    id = Column(Integer, primary_key=True, index=True)
    shopify_domain = Column(String, unique=True, index=True, nullable=False)
    shop_name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    
    # Store settings
    currency = Column(String, default="USD")
    timezone = Column(String, default="UTC")
    
    # Subscription info
    subscription_plan = Column(String, default="starter")  # starter, growth, pro
    subscription_status = Column(String, default="trial")  # trial, active, cancelled, expired, frozen
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    
    # Shopify Billing API integration
    shopify_charge_id = Column(String, nullable=True)  # Recurring charge ID
    billing_cycle_start = Column(DateTime(timezone=True), nullable=True)
    billing_cycle_end = Column(DateTime(timezone=True), nullable=True)
    plan_price = Column(Float, default=0.0)
    usage_charges = Column(Float, default=0.0)
    billing_currency = Column(String, default="USD")
    
    # GDPR compliance
    deletion_scheduled_at = Column(DateTime(timezone=True), nullable=True)
    
    # App status
    is_active = Column(Boolean, default=True)
    uninstalled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Access tokens (encrypted in production)
    access_token = Column(Text, nullable=False)
    
    # Relationships
    products = relationship("Product", back_populates="store", cascade="all, delete-orphan")
    locations = relationship("Location", back_populates="store", cascade="all, delete-orphan")
    inventory_items = relationship("InventoryItem", back_populates="store", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="store", cascade="all, delete-orphan")


class Location(Base, TimestampMixin):
    """Store locations (warehouses, retail stores, etc.)"""
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    shopify_location_id = Column(String, index=True, nullable=False)
    
    name = Column(String, nullable=False)
    address = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    country = Column(String, nullable=True)
    
    # Location settings
    is_active = Column(Boolean, default=True)
    manages_inventory = Column(Boolean, default=True)
    
    # Relationships
    store = relationship("Store", back_populates="locations")
    inventory_items = relationship("InventoryItem", back_populates="location")


class Product(Base, TimestampMixin):
    """Shopify products"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    shopify_product_id = Column(String, index=True, nullable=False)
    
    # Product details
    title = Column(String, nullable=False)
    handle = Column(String, nullable=False)
    product_type = Column(String, nullable=True)
    vendor = Column(String, nullable=True)
    tags = Column(Text, nullable=True)  # Comma-separated tags
    body_html = Column(Text, nullable=True)  # Product description HTML
    
    # Pricing
    price = Column(Float, nullable=True)
    cost_per_item = Column(Float, nullable=True)
    
    # Status
    status = Column(String, default="active")  # active, archived, draft
    
    # Custom fields data (JSONB for flexibility + SQL queries)
    custom_data = Column(JSON, default={})  # Store custom field values
    
    # Relationships
    store = relationship("Store", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")


class ProductVariant(Base, TimestampMixin):
    """Product variants (size, color, etc.)"""
    __tablename__ = "product_variants"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    shopify_variant_id = Column(String, index=True, nullable=False)
    
    # Variant details
    title = Column(String, nullable=False)
    sku = Column(String, nullable=True, index=True)
    barcode = Column(String, nullable=True)
    option1 = Column(String, nullable=True)  # e.g., Size
    option2 = Column(String, nullable=True)  # e.g., Color
    option3 = Column(String, nullable=True)  # e.g., Style
    
    # Pricing
    price = Column(Float, nullable=False)
    compare_at_price = Column(Float, nullable=True)
    cost_per_item = Column(Float, nullable=True)
    
    # Physical properties
    weight = Column(Float, nullable=True)
    weight_unit = Column(String, default="kg")
    
    # Inventory settings
    requires_shipping = Column(Boolean, default=True)
    track_inventory = Column(Boolean, default=True)
    inventory_policy = Column(String, default="deny")  # deny, continue
    inventory_quantity = Column(Integer, default=0)
    inventory_management = Column(String, nullable=True)  # shopify, manual, etc.
    
    # Custom fields data
    custom_data = Column(JSON, default={})
    
    # Relationships
    product = relationship("Product", back_populates="variants")
    inventory_items = relationship("InventoryItem", back_populates="variant")


class InventoryItem(Base, TimestampMixin):
    """Inventory levels per variant per location"""
    __tablename__ = "inventory_items"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=False)
    
    # Current inventory
    available_quantity = Column(Integer, default=0)
    committed_quantity = Column(Integer, default=0)  # Reserved for orders
    on_hand_quantity = Column(Integer, default=0)  # Physical stock
    
    # Reorder settings
    reorder_point = Column(Integer, default=10)
    reorder_quantity = Column(Integer, default=50)
    max_stock_level = Column(Integer, nullable=True)
    
    # Lead times
    lead_time_days = Column(Integer, default=7)
    
    # Custom fields data
    custom_data = Column(JSON, default={})
    
    # Relationships
    store = relationship("Store", back_populates="inventory_items")
    location = relationship("Location", back_populates="inventory_items")
    variant = relationship("ProductVariant", back_populates="inventory_items")
    movements = relationship("InventoryMovement", back_populates="inventory_item")


class InventoryMovement(Base, TimestampMixin):
    """Inventory movement history"""
    __tablename__ = "inventory_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    
    # Movement details
    movement_type = Column(String, nullable=False)  # purchase, sale, adjustment, transfer
    quantity_change = Column(Integer, nullable=False)  # Positive or negative
    reference_id = Column(String, nullable=True)  # Order ID, PO number, etc.
    
    # Cost tracking
    unit_cost = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    inventory_item = relationship("InventoryItem", back_populates="movements")


class Alert(Base, TimestampMixin):
    """Smart alerts for inventory management"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    
    # Alert details
    alert_type = Column(String, nullable=False)  # low_stock, overstock, reorder, compliance, workflow, custom
    severity = Column(String, default="medium")  # low, medium, high, critical
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    
    # Alert data
    product_sku = Column(String, nullable=True)
    location_name = Column(String, nullable=True)
    current_stock = Column(Integer, nullable=True)
    recommended_action = Column(Text, nullable=True)
    
    # Enhanced alert features
    alert_source = Column(String, default="system")  # system, workflow, manual, api
    entity_type = Column(String, nullable=True)  # product, variant, inventory_item, supplier
    entity_id = Column(Integer, nullable=True)
    custom_data = Column(JSON, default={})  # Store custom alert data
    notification_channels = Column(JSON, default=[])  # ["email", "webhook", "sms"]
    
    # Status
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String, nullable=True)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Auto-resolution
    auto_resolve_at = Column(DateTime(timezone=True), nullable=True)
    is_auto_resolvable = Column(Boolean, default=False)
    
    # Relationships
    store = relationship("Store", back_populates="alerts")


class AlertTemplate(Base, TimestampMixin):
    """User-defined alert templates for custom alerts"""
    __tablename__ = "alert_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    
    # Template definition
    template_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    alert_type = Column(String, nullable=False)
    
    # Template configuration
    title_template = Column(String, nullable=False)  # "Low Stock: {product_name}"
    message_template = Column(Text, nullable=False)  # "Stock for {sku} is {current_stock}"
    severity = Column(String, default="medium")
    
    # Trigger conditions
    trigger_conditions = Column(JSON, default={})  # Same format as workflow conditions
    
    # Notification settings
    notification_channels = Column(JSON, default=[])  # ["email", "webhook"]
    notification_config = Column(JSON, default={})  # Email addresses, webhook URLs, etc.
    
    # Template settings
    is_active = Column(Boolean, default=True)
    auto_resolve_hours = Column(Integer, nullable=True)  # Auto-resolve after X hours
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    store = relationship("Store")


class Forecast(Base, TimestampMixin):
    """Sales forecasting data"""
    __tablename__ = "forecasts"
    
    id = Column(Integer, primary_key=True, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    
    # Forecast period
    forecast_date = Column(DateTime(timezone=True), nullable=False)
    forecast_period = Column(String, default="daily")  # daily, weekly, monthly
    
    # Predictions
    predicted_demand = Column(Float, nullable=False)
    confidence_level = Column(Float, default=0.8)  # 0.0 to 1.0
    
    # Historical data used
    historical_days = Column(Integer, default=90)
    seasonal_factor = Column(Float, default=1.0)
    trend_factor = Column(Float, default=1.0)
    
    # Model info
    model_version = Column(String, default="v1")
    accuracy_score = Column(Float, nullable=True)


class Supplier(Base, TimestampMixin):
    """Supplier information"""
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    
    # Supplier details
    name = Column(String, nullable=False)
    contact_person = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    
    # Address
    address = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    country = Column(String, nullable=True)
    
    # Business terms
    payment_terms = Column(String, nullable=True)  # Net 30, COD, etc.
    minimum_order_value = Column(Float, nullable=True)
    lead_time_days = Column(Integer, default=14)
    
    # Performance metrics
    reliability_score = Column(Float, default=5.0)  # 1-10 scale
    quality_score = Column(Float, default=5.0)
    
    # Status
    is_active = Column(Boolean, default=True)


class PurchaseOrder(Base, TimestampMixin):
    """Purchase orders to suppliers"""
    __tablename__ = "purchase_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    
    # PO details
    po_number = Column(String, unique=True, nullable=False)
    status = Column(String, default="draft")  # draft, sent, confirmed, received, cancelled
    
    # Dates
    order_date = Column(DateTime(timezone=True), default=func.now())
    expected_delivery_date = Column(DateTime(timezone=True), nullable=True)
    actual_delivery_date = Column(DateTime(timezone=True), nullable=True)
    
    # Financial
    subtotal = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    shipping_cost = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    line_items = relationship("PurchaseOrderLineItem", back_populates="purchase_order")


class PurchaseOrderLineItem(Base, TimestampMixin):
    """Line items in purchase orders"""
    __tablename__ = "purchase_order_line_items"
    
    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=False)
    
    # Line item details
    quantity_ordered = Column(Integer, nullable=False)
    quantity_received = Column(Integer, default=0)
    unit_cost = Column(Float, nullable=False)
    line_total = Column(Float, nullable=False)
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="line_items")


# =============================================================================
# CUSTOM FIELDS SYSTEM - Our competitive advantage vs $2,500 enterprise tools
# =============================================================================

class CustomFieldDefinition(Base, TimestampMixin):
    """Define custom field schemas for any entity"""
    __tablename__ = "custom_field_definitions"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    
    # Field definition
    field_name = Column(String, nullable=False)  # e.g. "season", "material", "supplier_rating"
    display_name = Column(String, nullable=False)  # e.g. "Season", "Material Type", "Supplier Rating"
    field_type = Column(String, nullable=False)  # text, number, date, boolean, select, multi_select, url, email
    target_entity = Column(String, nullable=False)  # "product", "variant", "inventory_item", "supplier"
    
    # Validation rules (stored as JSON)
    validation_rules = Column(JSON, default={})  # {"min": 0, "max": 100, "options": ["S", "M", "L"], "regex": "pattern"}
    
    # Field settings
    is_required = Column(Boolean, default=False)
    is_searchable = Column(Boolean, default=True)
    is_filterable = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    help_text = Column(Text, nullable=True)
    default_value = Column(String, nullable=True)
    
    # Grouping and organization
    field_group = Column(String, nullable=True)  # "basic", "advanced", "cultural", "compliance"
    industry_template = Column(String, nullable=True)  # "fashion", "food", "electronics", "B2B"
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    store = relationship("Store")


class WorkflowRule(Base, TimestampMixin):
    """Custom business logic rules and automation"""
    __tablename__ = "workflow_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    
    # Rule definition
    rule_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Trigger configuration
    trigger_event = Column(String, nullable=False)  # "inventory_low", "custom_field_change", "product_created", etc.
    trigger_conditions = Column(JSON, default={})  # Complex conditions as JSON
    
    # Actions to perform
    actions = Column(JSON, default=[])  # [{"type": "alert", "message": "Low stock!"}, {"type": "webhook", "url": "..."}]
    
    # Rule settings
    is_active = Column(Boolean, default=True)
    execution_count = Column(Integer, default=0)
    last_executed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Priority and limits
    priority = Column(Integer, default=100)  # Lower number = higher priority
    max_executions_per_hour = Column(Integer, default=60)
    
    # Relationships
    store = relationship("Store")


class WorkflowExecution(Base, TimestampMixin):
    """Log of workflow rule executions"""
    __tablename__ = "workflow_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("workflow_rules.id"), nullable=False)
    
    # Execution details
    trigger_data = Column(JSON, default={})  # Data that triggered the rule
    execution_status = Column(String, default="success")  # success, failed, skipped
    error_message = Column(Text, nullable=True)
    
    # Performance metrics
    execution_time_ms = Column(Integer, nullable=True)
    
    # Relationships
    rule = relationship("WorkflowRule")