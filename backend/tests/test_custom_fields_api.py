"""
Test suite for Custom Fields API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestCustomFieldsAPI:
    """Test cases for custom fields endpoints"""

    def test_list_all_custom_fields(self):
        """Test endpoint for listing all custom fields"""
        response = client.get("/api/custom-fields/")
        
        assert response.status_code == 200
        data = response.json()
        assert "fields" in data
        assert "total" in data

    def test_get_shop_custom_fields(self):
        """Test getting custom fields for a specific shop"""
        shop_domain = "test-shop.myshopify.com"
        response = client.get(f"/api/custom-fields/{shop_domain}")
        
        assert response.status_code == 200
        data = response.json()
        assert "shop_domain" in data
        assert data["shop_domain"] == shop_domain
        assert "fields" in data

    def test_create_custom_field_success(self):
        """Test successful creation of a custom field"""
        shop_domain = "new-shop.myshopify.com"
        field_data = {
            "field_name": "new_field",
            "display_name": "New Field",
            "field_type": "text",
            "target_entity": "product"
        }
        
        response = client.post(f"/api/custom-fields/{shop_domain}", json=field_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "field" in data

    def test_create_custom_field_missing_field_name(self):
        """Test creation of custom field with missing field name"""
        shop_domain = "new-shop.myshopify.com"
        field_data = {"display_name": "No Field Name"}
        
        response = client.post(f"/api/custom-fields/{shop_domain}", json=field_data)
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "field_name is required"

    def test_apply_existing_template(self):
        """Test application of an existing template"""
        template_name = "apparel"
        shop_domain = "template-shop.myshopify.com"
        response = client.post(f"/api/custom-fields/templates/{template_name}/apply/{shop_domain}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "fields_created" in data

    def test_apply_nonexistent_template(self):
        """Test application of a non-existent template"""
        template_name = "nonexistent"
        shop_domain = "template-shop.myshopify.com"
        response = client.post(f"/api/custom-fields/templates/{template_name}/apply/{shop_domain}")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == f"Template '{template_name}' not found"

    def test_delete_custom_field_success(self):
        """Test successful deletion of a custom field"""
        shop_domain = "deletion-shop.myshopify.com"
        field_id = "existing_field"
        
        # Assume field exists
        client.post(f"/api/custom-fields/{shop_domain}", json={"field_name": field_id, "display_name": "Delete Me"})
        response = client.delete(f"/api/custom-fields/{shop_domain}/{field_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Custom field deleted successfully"

    def test_delete_custom_field_not_found(self):
        """Test deletion of a non-existent custom field"""
        shop_domain = "deletion-shop.myshopify.com"
        field_id = "nonexistent_field"
        response = client.delete(f"/api/custom-fields/{shop_domain}/{field_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Field not found"
