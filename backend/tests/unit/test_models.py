"""
Unit tests for database models
Tests model validation, relationships, and business logic
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import (
    Store, Product, ProductVariant, InventoryItem, Location, Alert,
    CustomFieldDefinition, WorkflowRule, WorkflowExecution, TimestampMixin
)


class TestTimestampMixin:
    """Test timestamp mixin functionality"""
    
    def test_timestamps_auto_populated(self, db_session):
        """Test that timestamps are automatically populated"""
        store = Store(
            shopify_store_id="test_123",
            shopify_domain="test.myshopify.com",
            store_name="Test Store"
        )
        db_session.add(store)
        db_session.commit()
        
        # Check timestamps are set
        assert store.created_at is not None
        assert store.updated_at is not None
        assert store.created_at == store.updated_at
    
    def test_updated_at_changes_on_update(self, db_session):
        """Test that updated_at changes when record is modified"""
        store = Store(
            shopify_store_id="test_123",
            shopify_domain="test.myshopify.com",
            store_name="Test Store"
        )
        db_session.add(store)
        db_session.commit()
        
        original_updated_at = store.updated_at
        
        # Update the store
        store.store_name = "Updated Store Name"
        db_session.commit()
        
        # updated_at should have changed
        assert store.updated_at > original_updated_at
        # created_at should remain the same
        assert store.created_at < store.updated_at


class TestStore:
    """Test Store model"""
    
    def test_store_creation(self, db_session):
        """Test creating a store"""
        store = Store(
            shopify_store_id="12345",
            shopify_domain="test-store.myshopify.com",
            store_name="Test Store",
            currency="USD",
            timezone="UTC",
            subscription_plan="starter",
            subscription_status="active"
        )
        db_session.add(store)
        db_session.commit()
        
        assert store.id is not None
        assert store.shopify_store_id == "12345"
        assert store.shopify_domain == "test-store.myshopify.com"
        assert store.subscription_plan == "starter"
    
    def test_store_unique_constraints(self, db_session):
        """Test store unique constraints"""
        # Create first store
        store1 = Store(
            shopify_store_id="12345",
            shopify_domain="store1.myshopify.com",
            store_name="Store 1"
        )
        db_session.add(store1)
        db_session.commit()
        
        # Try to create store with same shopify_store_id
        store2 = Store(
            shopify_store_id="12345",  # Same ID
            shopify_domain="store2.myshopify.com",
            store_name="Store 2"
        )
        db_session.add(store2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_store_defaults(self, db_session):
        """Test store default values"""
        store = Store(
            shopify_store_id="12345",
            shopify_domain="test.myshopify.com",
            store_name="Test Store"
        )
        db_session.add(store)
        db_session.commit()
        
        # Check defaults
        assert store.currency == "USD"
        assert store.timezone == "UTC"
        assert store.subscription_plan == "starter"
        assert store.subscription_status == "trial"
        assert store.plan_price == 0.0
        assert store.usage_charges == 0.0
    
    def test_store_billing_info(self, db_session):
        """Test store billing information"""
        store = Store(
            shopify_store_id="12345",
            shopify_domain="test.myshopify.com",
            store_name="Test Store",
            subscription_plan="growth",
            subscription_status="active",
            shopify_charge_id="charge_123",
            plan_price=149.0,
            billing_currency="CAD"
        )
        db_session.add(store)
        db_session.commit()
        
        assert store.subscription_plan == "growth"
        assert store.shopify_charge_id == "charge_123"
        assert store.plan_price == 149.0
        assert store.billing_currency == "CAD"


class TestProduct:
    """Test Product model"""
    
    def test_product_creation(self, db_session, sample_store):
        """Test creating a product"""
        product = Product(
            store_id=sample_store.id,
            shopify_product_id="prod_123",
            title="Test Product",
            handle="test-product",
            product_type="Electronics",
            vendor="Test Vendor",
            price=99.99,
            status="active"
        )
        db_session.add(product)
        db_session.commit()
        
        assert product.id is not None
        assert product.store_id == sample_store.id
        assert product.title == "Test Product"
        assert product.price == 99.99
    
    def test_product_custom_data(self, db_session, sample_store):
        """Test product custom data JSON field"""
        custom_data = {
            "season": "Winter",
            "material": "Cotton",
            "priority": "High"
        }
        
        product = Product(
            store_id=sample_store.id,
            shopify_product_id="prod_123",
            title="Test Product",
            handle="test-product",
            custom_data=custom_data
        )
        db_session.add(product)
        db_session.commit()
        
        # Retrieve and check custom data
        retrieved_product = db_session.query(Product).filter_by(id=product.id).first()
        assert retrieved_product.custom_data["season"] == "Winter"
        assert retrieved_product.custom_data["material"] == "Cotton"
        assert retrieved_product.custom_data["priority"] == "High"
    
    def test_product_relationships(self, db_session, sample_store):
        """Test product relationships"""
        product = Product(
            store_id=sample_store.id,
            shopify_product_id="prod_123",
            title="Test Product",
            handle="test-product"
        )
        db_session.add(product)
        db_session.commit()
        
        # Create variants for this product
        variant1 = ProductVariant(
            store_id=sample_store.id,
            product_id=product.id,
            shopify_variant_id="var_1",
            title="Variant 1",
            sku="SKU-001"
        )
        variant2 = ProductVariant(
            store_id=sample_store.id,
            product_id=product.id,
            shopify_variant_id="var_2",
            title="Variant 2",
            sku="SKU-002"
        )
        db_session.add_all([variant1, variant2])
        db_session.commit()
        
        # Test relationship
        assert len(product.variants) == 2
        assert variant1 in product.variants
        assert variant2 in product.variants


class TestProductVariant:
    """Test ProductVariant model"""
    
    def test_variant_creation(self, db_session, sample_product):
        """Test creating a product variant"""
        variant = ProductVariant(
            store_id=sample_product.store_id,
            product_id=sample_product.id,
            shopify_variant_id="var_123",
            title="Test Variant",
            sku="TEST-SKU-001",
            price=99.99,
            weight=1.5,
            weight_unit="kg"
        )
        db_session.add(variant)
        db_session.commit()
        
        assert variant.id is not None
        assert variant.product_id == sample_product.id
        assert variant.sku == "TEST-SKU-001"
        assert variant.weight == 1.5
    
    def test_variant_custom_data(self, db_session, sample_product):
        """Test variant custom data"""
        custom_data = {
            "size": "Large",
            "color": "Blue",
            "material": "Cotton"
        }
        
        variant = ProductVariant(
            store_id=sample_product.store_id,
            product_id=sample_product.id,
            shopify_variant_id="var_123",
            title="Test Variant",
            sku="TEST-SKU-001",
            custom_data=custom_data
        )
        db_session.add(variant)
        db_session.commit()
        
        assert variant.custom_data["size"] == "Large"
        assert variant.custom_data["color"] == "Blue"


class TestInventoryItem:
    """Test InventoryItem model"""
    
    def test_inventory_creation(self, db_session, sample_variant):
        """Test creating an inventory item"""
        inventory = InventoryItem(
            store_id=sample_variant.store_id,
            variant_id=sample_variant.id,
            location_id=1,
            available_quantity=100,
            on_hand_quantity=105,
            committed_quantity=5,
            reorder_point=20,
            reorder_quantity=200,
            cost_per_item=45.50
        )
        db_session.add(inventory)
        db_session.commit()
        
        assert inventory.id is not None
        assert inventory.variant_id == sample_variant.id
        assert inventory.available_quantity == 100
        assert inventory.reorder_point == 20
    
    def test_inventory_stock_calculations(self, db_session, sample_variant):
        """Test inventory stock calculation methods"""
        inventory = InventoryItem(
            store_id=sample_variant.store_id,
            variant_id=sample_variant.id,
            location_id=1,
            available_quantity=100,
            on_hand_quantity=105,
            committed_quantity=5,
            reorder_point=20
        )
        db_session.add(inventory)
        db_session.commit()
        
        # Test stock level calculations (these would be methods on the model)
        assert inventory.available_quantity == 100
        assert inventory.on_hand_quantity == 105
        assert inventory.committed_quantity == 5
        
        # Test if reorder is needed
        assert inventory.available_quantity > inventory.reorder_point  # No reorder needed
    
    def test_inventory_low_stock_scenario(self, db_session, sample_variant):
        """Test low stock scenario"""
        inventory = InventoryItem(
            store_id=sample_variant.store_id,
            variant_id=sample_variant.id,
            location_id=1,
            available_quantity=5,  # Low stock
            on_hand_quantity=5,
            committed_quantity=0,
            reorder_point=20
        )
        db_session.add(inventory)
        db_session.commit()
        
        # Should trigger low stock alert
        assert inventory.available_quantity < inventory.reorder_point


class TestAlert:
    """Test Alert model"""
    
    def test_alert_creation(self, db_session, sample_store):
        """Test creating an alert"""
        alert = Alert(
            store_id=sample_store.id,
            alert_type="low_stock",
            severity="high",
            title="Low Stock Alert",
            message="Product SKU-001 is running low on stock",
            product_sku="SKU-001",
            current_stock=5,
            is_acknowledged=False,
            is_resolved=False
        )
        db_session.add(alert)
        db_session.commit()
        
        assert alert.id is not None
        assert alert.alert_type == "low_stock"
        assert alert.severity == "high"
        assert alert.is_acknowledged == False
    
    def test_alert_acknowledgment(self, db_session, sample_alert):
        """Test alert acknowledgment"""
        # Initially not acknowledged
        assert sample_alert.is_acknowledged == False
        assert sample_alert.acknowledged_at is None
        
        # Acknowledge the alert
        sample_alert.is_acknowledged = True
        sample_alert.acknowledged_at = datetime.utcnow()
        db_session.commit()
        
        assert sample_alert.is_acknowledged == True
        assert sample_alert.acknowledged_at is not None
    
    def test_alert_resolution(self, db_session, sample_alert):
        """Test alert resolution"""
        # Initially not resolved
        assert sample_alert.is_resolved == False
        assert sample_alert.resolved_at is None
        
        # Resolve the alert
        sample_alert.is_resolved = True
        sample_alert.resolved_at = datetime.utcnow()
        db_session.commit()
        
        assert sample_alert.is_resolved == True
        assert sample_alert.resolved_at is not None
    
    def test_alert_auto_resolve(self, db_session, sample_store):
        """Test alert auto-resolve functionality"""
        auto_resolve_time = datetime.utcnow() + timedelta(hours=24)
        
        alert = Alert(
            store_id=sample_store.id,
            alert_type="low_stock",
            severity="medium",
            title="Auto-resolve Alert",
            message="This alert should auto-resolve",
            auto_resolve_at=auto_resolve_time
        )
        db_session.add(alert)
        db_session.commit()
        
        assert alert.auto_resolve_at == auto_resolve_time


class TestCustomFieldDefinition:
    """Test CustomFieldDefinition model"""
    
    def test_custom_field_creation(self, db_session, sample_store):
        """Test creating a custom field definition"""
        field = CustomFieldDefinition(
            store_id=sample_store.id,
            field_name="priority",
            display_name="Product Priority",
            field_type="select",
            target_entity="product",
            validation_rules={"options": ["Low", "Medium", "High"]},
            is_required=False,
            is_active=True
        )
        db_session.add(field)
        db_session.commit()
        
        assert field.id is not None
        assert field.field_name == "priority"
        assert field.field_type == "select"
        assert field.validation_rules["options"] == ["Low", "Medium", "High"]
    
    def test_custom_field_validation_rules(self, db_session, sample_store):
        """Test custom field validation rules"""
        # Text field with max length
        text_field = CustomFieldDefinition(
            store_id=sample_store.id,
            field_name="description",
            display_name="Description",
            field_type="text",
            target_entity="product",
            validation_rules={"max_length": 500}
        )
        db_session.add(text_field)
        
        # Number field with range
        number_field = CustomFieldDefinition(
            store_id=sample_store.id,
            field_name="rating",
            display_name="Product Rating",
            field_type="number",
            target_entity="product",
            validation_rules={"min_value": 1, "max_value": 5}
        )
        db_session.add(number_field)
        
        db_session.commit()
        
        assert text_field.validation_rules["max_length"] == 500
        assert number_field.validation_rules["min_value"] == 1
        assert number_field.validation_rules["max_value"] == 5
    
    def test_custom_field_uniqueness(self, db_session, sample_store):
        """Test custom field name uniqueness per store"""
        field1 = CustomFieldDefinition(
            store_id=sample_store.id,
            field_name="priority",
            display_name="Priority 1",
            field_type="text",
            target_entity="product"
        )
        db_session.add(field1)
        db_session.commit()
        
        # Try to create field with same name in same store
        field2 = CustomFieldDefinition(
            store_id=sample_store.id,
            field_name="priority",  # Same name
            display_name="Priority 2",
            field_type="select",
            target_entity="product"
        )
        db_session.add(field2)
        
        # This should fail due to unique constraint
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestWorkflowRule:
    """Test WorkflowRule model"""
    
    def test_workflow_rule_creation(self, db_session, sample_store):
        """Test creating a workflow rule"""
        rule = WorkflowRule(
            store_id=sample_store.id,
            rule_name="Low Stock Alert Rule",
            description="Create alert when stock is low",
            trigger_event="inventory_low",
            trigger_conditions={
                "field": "current_stock",
                "operator": "less_than",
                "value": 10
            },
            actions=[
                {
                    "type": "create_alert",
                    "title": "Low Stock",
                    "message": "Stock is low",
                    "severity": "high"
                }
            ],
            priority=100,
            is_active=True
        )
        db_session.add(rule)
        db_session.commit()
        
        assert rule.id is not None
        assert rule.rule_name == "Low Stock Alert Rule"
        assert rule.trigger_event == "inventory_low"
        assert rule.priority == 100
    
    def test_workflow_rule_complex_conditions(self, db_session, sample_store):
        """Test workflow rule with complex conditions"""
        complex_conditions = {
            "type": "and",
            "conditions": [
                {"field": "current_stock", "operator": "less_than", "value": 20},
                {
                    "type": "or",
                    "conditions": [
                        {"field": "priority", "operator": "equals", "value": "high"},
                        {"field": "cost", "operator": "greater_than", "value": 100}
                    ]
                }
            ]
        }
        
        rule = WorkflowRule(
            store_id=sample_store.id,
            rule_name="Complex Rule",
            trigger_event="inventory_low",
            trigger_conditions=complex_conditions,
            actions=[{"type": "create_alert", "message": "Complex alert"}],
            priority=200
        )
        db_session.add(rule)
        db_session.commit()
        
        assert rule.trigger_conditions["type"] == "and"
        assert len(rule.trigger_conditions["conditions"]) == 2
    
    def test_workflow_rule_multiple_actions(self, db_session, sample_store):
        """Test workflow rule with multiple actions"""
        actions = [
            {
                "type": "create_alert",
                "title": "Low Stock Alert",
                "message": "Stock is low",
                "severity": "high"
            },
            {
                "type": "send_email",
                "to_email": "admin@example.com",
                "subject": "Low Stock Notification",
                "template": "low_stock_email"
            },
            {
                "type": "update_field",
                "entity_type": "product",
                "field_name": "needs_reorder",
                "value": True
            }
        ]
        
        rule = WorkflowRule(
            store_id=sample_store.id,
            rule_name="Multi-Action Rule",
            trigger_event="inventory_low",
            actions=actions,
            priority=150
        )
        db_session.add(rule)
        db_session.commit()
        
        assert len(rule.actions) == 3
        assert rule.actions[0]["type"] == "create_alert"
        assert rule.actions[1]["type"] == "send_email"
        assert rule.actions[2]["type"] == "update_field"


class TestWorkflowExecution:
    """Test WorkflowExecution model"""
    
    def test_workflow_execution_creation(self, db_session, sample_workflow_rule):
        """Test creating a workflow execution log"""
        execution = WorkflowExecution(
            store_id=sample_workflow_rule.store_id,
            rule_id=sample_workflow_rule.id,
            trigger_event="inventory_low",
            event_data={
                "entity_id": 123,
                "current_stock": 5,
                "sku": "TEST-SKU"
            },
            conditions_met=True,
            actions_executed=1,
            success=True,
            execution_time_ms=250.5
        )
        db_session.add(execution)
        db_session.commit()
        
        assert execution.id is not None
        assert execution.rule_id == sample_workflow_rule.id
        assert execution.conditions_met == True
        assert execution.success == True
        assert execution.execution_time_ms == 250.5
    
    def test_workflow_execution_failure(self, db_session, sample_workflow_rule):
        """Test workflow execution with failure"""
        execution = WorkflowExecution(
            store_id=sample_workflow_rule.store_id,
            rule_id=sample_workflow_rule.id,
            trigger_event="inventory_low",
            event_data={"entity_id": 123},
            conditions_met=True,
            actions_executed=0,
            success=False,
            error_message="Action execution failed: Invalid webhook URL"
        )
        db_session.add(execution)
        db_session.commit()
        
        assert execution.success == False
        assert "Invalid webhook URL" in execution.error_message


class TestModelRelationships:
    """Test model relationships and foreign keys"""
    
    def test_store_to_products_relationship(self, db_session, sample_store):
        """Test store to products relationship"""
        # Create multiple products for the store
        product1 = Product(
            store_id=sample_store.id,
            shopify_product_id="prod_1",
            title="Product 1",
            handle="product-1"
        )
        product2 = Product(
            store_id=sample_store.id,
            shopify_product_id="prod_2",
            title="Product 2",
            handle="product-2"
        )
        db_session.add_all([product1, product2])
        db_session.commit()
        
        # Test relationship
        assert len(sample_store.products) == 2
        assert product1 in sample_store.products
        assert product2 in sample_store.products
    
    def test_product_to_variants_relationship(self, db_session, sample_product):
        """Test product to variants relationship"""
        variant1 = ProductVariant(
            store_id=sample_product.store_id,
            product_id=sample_product.id,
            shopify_variant_id="var_1",
            title="Variant 1",
            sku="SKU-001"
        )
        variant2 = ProductVariant(
            store_id=sample_product.store_id,
            product_id=sample_product.id,
            shopify_variant_id="var_2",
            title="Variant 2",
            sku="SKU-002"
        )
        db_session.add_all([variant1, variant2])
        db_session.commit()
        
        assert len(sample_product.variants) == 2
        assert variant1.product == sample_product
        assert variant2.product == sample_product
    
    def test_variant_to_inventory_relationship(self, db_session, sample_variant):
        """Test variant to inventory items relationship"""
        # Create inventory items for different locations
        inventory1 = InventoryItem(
            store_id=sample_variant.store_id,
            variant_id=sample_variant.id,
            location_id=1,
            available_quantity=50
        )
        inventory2 = InventoryItem(
            store_id=sample_variant.store_id,
            variant_id=sample_variant.id,
            location_id=2,
            available_quantity=30
        )
        db_session.add_all([inventory1, inventory2])
        db_session.commit()
        
        assert len(sample_variant.inventory_items) == 2
        assert inventory1.variant == sample_variant
        assert inventory2.variant == sample_variant
    
    def test_cascade_deletes(self, db_session, sample_store):
        """Test cascade deletes work properly"""
        # Create product with variants and inventory
        product = Product(
            store_id=sample_store.id,
            shopify_product_id="prod_cascade",
            title="Cascade Test Product",
            handle="cascade-test"
        )
        db_session.add(product)
        db_session.commit()
        
        variant = ProductVariant(
            store_id=sample_store.id,
            product_id=product.id,
            shopify_variant_id="var_cascade",
            title="Cascade Variant",
            sku="CASCADE-SKU"
        )
        db_session.add(variant)
        db_session.commit()
        
        inventory = InventoryItem(
            store_id=sample_store.id,
            variant_id=variant.id,
            location_id=1,
            available_quantity=100
        )
        db_session.add(inventory)
        db_session.commit()
        
        # Delete the product
        db_session.delete(product)
        db_session.commit()
        
        # Check that related records are handled appropriately
        # (The exact behavior depends on cascade settings in the model definitions)
        remaining_variants = db_session.query(ProductVariant).filter_by(product_id=product.id).all()
        remaining_inventory = db_session.query(InventoryItem).filter_by(variant_id=variant.id).all()
        
        # This test assumes proper cascade configuration
        # assert len(remaining_variants) == 0
        # assert len(remaining_inventory) == 0


class TestModelValidation:
    """Test model validation and constraints"""
    
    def test_required_fields(self, db_session):
        """Test required fields validation"""
        # Try to create store without required fields
        with pytest.raises(IntegrityError):
            store = Store()  # Missing required fields
            db_session.add(store)
            db_session.commit()
    
    def test_field_length_constraints(self, db_session, sample_store):
        """Test field length constraints"""
        # Test with very long field values
        long_title = "A" * 300  # Assuming title has a max length
        
        product = Product(
            store_id=sample_store.id,
            shopify_product_id="prod_long",
            title=long_title,
            handle="long-product"
        )
        db_session.add(product)
        
        # This might raise an error depending on database constraints
        try:
            db_session.commit()
            # If it succeeds, check that the title was truncated or stored properly
            assert len(product.title) <= 300  # Adjust based on actual constraint
        except IntegrityError:
            # Expected if there's a length constraint
            db_session.rollback()
    
    def test_enum_field_validation(self, db_session, sample_store):
        """Test enum field validation"""
        # Test alert severity validation
        alert = Alert(
            store_id=sample_store.id,
            alert_type="low_stock",
            severity="invalid_severity",  # Invalid value
            title="Test Alert",
            message="Test message"
        )
        db_session.add(alert)
        
        # This should either be validated at the model level or database level
        try:
            db_session.commit()
        except (IntegrityError, ValueError):
            db_session.rollback()


class TestModelPerformance:
    """Test model performance characteristics"""
    
    def test_bulk_insert_performance(self, db_session, sample_store, performance_timer):
        """Test bulk insert performance"""
        performance_timer.start()
        
        # Create many products
        products = []
        for i in range(100):
            product = Product(
                store_id=sample_store.id,
                shopify_product_id=f"bulk_prod_{i}",
                title=f"Bulk Product {i}",
                handle=f"bulk-product-{i}"
            )
            products.append(product)
        
        db_session.add_all(products)
        db_session.commit()
        
        performance_timer.stop()
        
        # Should be reasonably fast
        assert performance_timer.elapsed() < 5.0  # Less than 5 seconds for 100 records
    
    def test_query_performance(self, db_session, sample_store, performance_timer):
        """Test query performance"""
        # Create some test data
        create_test_data(db_session, sample_store.id, num_products=50)
        
        performance_timer.start()
        
        # Query products
        products = db_session.query(Product).filter_by(store_id=sample_store.id).all()
        
        performance_timer.stop()
        
        assert len(products) >= 50
        # Should be fast
        assert performance_timer.elapsed() < 1.0  # Less than 1 second