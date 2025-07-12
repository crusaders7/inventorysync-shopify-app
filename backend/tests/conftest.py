"""
Test configuration and fixtures for InventorySync
Provides common test setup, database fixtures, and mock data
"""

import pytest
import asyncio
import os
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import our application components
from main import app
from database import Base, get_db, AsyncSessionLocal
from models import Store, Product, ProductVariant, InventoryItem, Alert, CustomFieldDefinition, WorkflowRule
from utils.logging import logger


# Test database URL - using in-memory SQLite for speed
TEST_DATABASE_URL = "sqlite:///./test_inventorysync.db"

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=test_engine
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session():
    """Create a fresh database session for each test"""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    session = TestSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Clean up - drop all tables
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden database dependency"""
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(db_session):
    """Create an async test client"""
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


# =============================================================================
# SAMPLE DATA FIXTURES
# =============================================================================

@pytest.fixture
def sample_store(db_session):
    """Create a sample store for testing"""
    store = Store(
        shopify_store_id="12345",
        shop_domain="test-store.myshopify.com",
        store_name="Test Store",
        currency="USD",
        timezone="UTC",
        subscription_plan="starter",
        subscription_status="active",
        plan_price=49.0
    )
    db_session.add(store)
    db_session.commit()
    db_session.refresh(store)
    return store


@pytest.fixture
def sample_product(db_session, sample_store):
    """Create a sample product for testing"""
    product = Product(
        store_id=sample_store.id,
        shopify_product_id="prod_123",
        title="Test Product",
        handle="test-product",
        product_type="Electronics",
        vendor="Test Vendor",
        price=99.99,
        status="active",
        custom_data={"season": "Winter", "material": "Cotton"}
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def sample_variant(db_session, sample_product):
    """Create a sample product variant for testing"""
    variant = ProductVariant(
        store_id=sample_product.store_id,
        product_id=sample_product.id,
        shopify_variant_id="var_456",
        title="Default Title",
        sku="TEST-SKU-001",
        price=99.99,
        weight=1.5,
        weight_unit="kg",
        custom_data={"size": "M", "color": "Blue"}
    )
    db_session.add(variant)
    db_session.commit()
    db_session.refresh(variant)
    return variant


@pytest.fixture
def sample_inventory_item(db_session, sample_variant):
    """Create a sample inventory item for testing"""
    inventory = InventoryItem(
        store_id=sample_variant.store_id,
        variant_id=sample_variant.id,
        location_id=1,
        available_quantity=50,
        on_hand_quantity=55,
        committed_quantity=5,
        reorder_point=20,
        reorder_quantity=100,
        cost_per_item=45.00,
        custom_data={"warehouse": "Main", "section": "A1"}
    )
    db_session.add(inventory)
    db_session.commit()
    db_session.refresh(inventory)
    return inventory


@pytest.fixture
def sample_custom_field(db_session, sample_store):
    """Create a sample custom field definition for testing"""
    field = CustomFieldDefinition(
        store_id=sample_store.id,
        field_name="priority",
        display_name="Product Priority",
        field_type="select",
        target_entity="product",
        validation_rules={"options": ["Low", "Medium", "High", "Critical"]},
        is_required=False,
        is_active=True
    )
    db_session.add(field)
    db_session.commit()
    db_session.refresh(field)
    return field


@pytest.fixture
def sample_workflow_rule(db_session, sample_store):
    """Create a sample workflow rule for testing"""
    rule = WorkflowRule(
        store_id=sample_store.id,
        rule_name="Low Stock Alert",
        description="Create alert when stock is low",
        trigger_event="inventory_low",
        trigger_conditions={
            "type": "and",
            "conditions": [
                {"field": "current_stock", "operator": "less_than", "value": 10}
            ]
        },
        actions=[
            {
                "type": "create_alert",
                "title": "Low Stock Alert",
                "message": "Stock for {sku} is low: {current_stock} units",
                "severity": "high"
            }
        ],
        priority=100,
        is_active=True
    )
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)
    return rule


@pytest.fixture
def sample_alert(db_session, sample_store):
    """Create a sample alert for testing"""
    alert = Alert(
        store_id=sample_store.id,
        alert_type="low_stock",
        severity="high",
        title="Low Stock Alert",
        message="Stock for TEST-SKU-001 is low: 5 units",
        product_sku="TEST-SKU-001",
        current_stock=5,
        is_acknowledged=False,
        is_resolved=False
    )
    db_session.add(alert)
    db_session.commit()
    db_session.refresh(alert)
    return alert


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

@pytest.fixture
def auth_headers():
    """Mock authentication headers for testing"""
    return {
        "Authorization": "Bearer test_token",
        "X-Shop-Domain": "test-store.myshopify.com"
    }


@pytest.fixture
def admin_headers():
    """Mock admin authentication headers for testing"""
    return {
        "X-Admin-Token": "test_admin_token"
    }


@pytest.fixture
def api_key_headers():
    """Mock API key headers for testing"""
    return {
        "X-API-Key": "isk_test_api_key_12345"
    }


def create_test_data(session, store_id: int, num_products: int = 5):
    """Helper function to create test data"""
    products = []
    
    for i in range(num_products):
        product = Product(
            store_id=store_id,
            shopify_product_id=f"prod_{i}",
            title=f"Test Product {i}",
            handle=f"test-product-{i}",
            product_type="Test Type",
            vendor="Test Vendor",
            price=float(10 + i * 10),
            status="active"
        )
        session.add(product)
        products.append(product)
    
    session.commit()
    return products


@pytest.fixture
def mock_shopify_response():
    """Mock Shopify API response data"""
    return {
        "product": {
            "id": 123456789,
            "title": "Test Product",
            "handle": "test-product",
            "product_type": "Electronics",
            "vendor": "Test Vendor",
            "variants": [
                {
                    "id": 987654321,
                    "title": "Default Title",
                    "sku": "TEST-SKU-001",
                    "price": "99.99",
                    "inventory_quantity": 50
                }
            ]
        }
    }


# =============================================================================
# TEST ENVIRONMENT SETUP
# =============================================================================

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "WARNING"
    os.environ["MONITORING_ENABLED"] = "false"
    
    yield
    
    # Cleanup
    for key in ["TESTING", "LOG_LEVEL", "MONITORING_ENABLED"]:
        if key in os.environ:
            del os.environ[key]


# =============================================================================
# ASYNC TEST HELPERS
# =============================================================================

@pytest.fixture
async def async_db_session():
    """Create an async database session for testing"""
    # For testing, we'll use the sync session but could be extended for async
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    session = TestSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Clean up - drop all tables
        Base.metadata.drop_all(bind=test_engine)


# =============================================================================
# PERFORMANCE TEST HELPERS
# =============================================================================

@pytest.fixture
def performance_timer():
    """Timer for performance testing"""
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            import time
            self.start_time = time.time()
        
        def stop(self):
            import time
            self.end_time = time.time()
        
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# =============================================================================
# MOCKING HELPERS
# =============================================================================

class MockShopifyClient:
    """Mock Shopify client for testing"""
    
    def __init__(self):
        self.responses = {}
        self.call_count = 0
    
    def set_response(self, endpoint: str, response: dict):
        self.responses[endpoint] = response
    
    async def get(self, endpoint: str, **kwargs):
        self.call_count += 1
        return self.responses.get(endpoint, {})
    
    async def post(self, endpoint: str, data: dict, **kwargs):
        self.call_count += 1
        return {"success": True, "data": data}


@pytest.fixture
def mock_shopify_client():
    """Provide a mock Shopify client"""
    return MockShopifyClient()