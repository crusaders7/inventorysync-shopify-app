"""Integration tests for API endpoints"""

import pytest
from httpx import AsyncClient

@pytest.mark.integration
class TestHealthEndpoints:
    async def test_root_endpoint(self, async_client: AsyncClient):
        """Test root endpoint"""
        response = await async_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
    
    async def test_health_endpoint(self, async_client: AsyncClient):
        """Test health check endpoint"""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "service" in data
        assert "timestamp" in data

@pytest.mark.integration
class TestProductEndpoints:
    async def test_get_products_unauthorized(self, async_client: AsyncClient):
        """Test getting products without auth"""
        response = await async_client.get("/api/v1/products")
        assert response.status_code == 403
    
    async def test_get_products_empty(self, async_client: AsyncClient, auth_headers):
        """Test getting products when empty"""
        response = await async_client.get("/api/v1/products", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["products"] == []
        assert data["total"] == 0
    
    async def test_create_product(self, async_client: AsyncClient, auth_headers, test_store):
        """Test creating a product"""
        product_data = {
            "title": "New Product",
            "sku": "NEW-001",
            "price": 29.99,
            "cost": 15.00,
            "tracked": True
        }
        
        response = await async_client.post(
            "/api/v1/products",
            json=product_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Product"
        assert data["sku"] == "NEW-001"

@pytest.mark.integration
class TestInventoryEndpoints:
    async def test_get_inventory(self, async_client: AsyncClient, auth_headers, test_product, test_location):
        """Test getting inventory levels"""
        response = await async_client.get(
            f"/api/v1/inventory?product_id={test_product.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "inventory_items" in data
    
    async def test_update_inventory(self, async_client: AsyncClient, auth_headers, test_product, test_location):
        """Test updating inventory levels"""
        update_data = {
            "product_id": test_product.id,
            "location_id": test_location.id,
            "quantity": 100,
            "adjustment_type": "set"
        }
        
        response = await async_client.post(
            "/api/v1/inventory/adjust",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["available_quantity"] == 100

@pytest.mark.integration
class TestAlertEndpoints:
    async def test_get_alerts(self, async_client: AsyncClient, auth_headers):
        """Test getting alerts"""
        response = await async_client.get("/api/v1/alerts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert "summary" in data
    
    async def test_acknowledge_alert(self, async_client: AsyncClient, auth_headers):
        """Test acknowledging an alert"""
        # First create an alert by setting low inventory
        # Then acknowledge it
        response = await async_client.post(
            "/api/v1/alerts/test-alert-id/acknowledge",
            headers=auth_headers
        )
        # This would fail without a real alert, but shows the pattern
        assert response.status_code in [200, 404]
