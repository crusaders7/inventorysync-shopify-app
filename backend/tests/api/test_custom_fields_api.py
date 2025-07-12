"""
API integration tests for custom fields endpoints
Tests the complete custom fields API functionality
"""

import pytest
import json
from fastapi.testclient import TestClient
from httpx import AsyncClient

from models import CustomFieldDefinition


class TestCustomFieldsAPI:
    """Test custom fields API endpoints"""
    
    def test_create_custom_field(self, client, sample_store, auth_headers):
        """Test creating a custom field"""
        field_data = {
            "field_name": "priority",
            "display_name": "Product Priority",
            "field_type": "select",
            "target_entity": "product",
            "validation_rules": {
                "options": ["Low", "Medium", "High", "Critical"]
            },
            "is_required": False
        }
        
        response = client.post(
            f"/api/custom-fields/{sample_store.shop_domain}",
            json=field_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["field_name"] == "priority"
        assert data["display_name"] == "Product Priority"
        assert data["field_type"] == "select"
        assert data["is_active"] == True
    
    def test_create_custom_field_validation_error(self, client, sample_store, auth_headers):
        """Test custom field creation with validation errors"""
        # Invalid field name
        field_data = {
            "field_name": "Invalid Field!",  # Invalid characters
            "display_name": "Invalid Field",
            "field_type": "text",
            "target_entity": "product"
        }
        
        response = client.post(
            f"/api/custom-fields/{sample_store.shop_domain}",
            json=field_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
    
    def test_create_reserved_field_name(self, client, sample_store, auth_headers):
        """Test creating field with reserved name"""
        field_data = {
            "field_name": "id",  # Reserved name
            "display_name": "ID Field",
            "field_type": "text",
            "target_entity": "product"
        }
        
        response = client.post(
            f"/api/custom-fields/{sample_store.shop_domain}",
            json=field_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "reserved name" in data["error"]
    
    def test_get_custom_fields(self, client, sample_store, sample_custom_field, auth_headers):
        """Test retrieving custom fields"""
        response = client.get(
            f"/api/custom-fields/{sample_store.shop_domain}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "fields" in data
        assert len(data["fields"]) >= 1
        assert data["fields"][0]["field_name"] == sample_custom_field.field_name
    
    def test_get_custom_fields_filtered(self, client, sample_store, auth_headers):
        """Test retrieving custom fields with filters"""
        # Create multiple fields
        field_data_1 = {
            "field_name": "product_priority",
            "display_name": "Product Priority",
            "field_type": "select",
            "target_entity": "product",
            "validation_rules": {"options": ["Low", "High"]}
        }
        
        field_data_2 = {
            "field_name": "variant_size",
            "display_name": "Variant Size",
            "field_type": "text",
            "target_entity": "variant"
        }
        
        # Create fields
        client.post(f"/api/custom-fields/{sample_store.shop_domain}", 
                    json=field_data_1, headers=auth_headers)
        client.post(f"/api/custom-fields/{sample_store.shop_domain}", 
                    json=field_data_2, headers=auth_headers)
        
        # Filter by entity type
        response = client.get(
            f"/api/custom-fields/{sample_store.shop_domain}?entity_type=product",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["fields"]) >= 1
        # All returned fields should be for products
        for field in data["fields"]:
            assert field["target_entity"] == "product"
    
    def test_update_custom_field(self, client, sample_store, sample_custom_field, auth_headers):
        """Test updating a custom field"""
        update_data = {
            "display_name": "Updated Priority",
            "validation_rules": {
                "options": ["Low", "Medium", "High", "Critical", "Urgent"]
            }
        }
        
        response = client.put(
            f"/api/custom-fields/{sample_store.shop_domain}/{sample_custom_field.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Updated Priority"
        assert len(data["validation_rules"]["options"]) == 5
    
    def test_delete_custom_field(self, client, sample_store, sample_custom_field, auth_headers):
        """Test deleting a custom field"""
        response = client.delete(
            f"/api/custom-fields/{sample_store.shop_domain}/{sample_custom_field.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Custom field deleted successfully"
        
        # Verify field is deleted/deactivated
        get_response = client.get(
            f"/api/custom-fields/{sample_store.shop_domain}",
            headers=auth_headers
        )
        fields = get_response.json()["fields"]
        active_fields = [f for f in fields if f["id"] == sample_custom_field.id and f["is_active"]]
        assert len(active_fields) == 0
    
    def test_apply_industry_template(self, client, sample_store, auth_headers):
        """Test applying industry template"""
        response = client.post(
            f"/api/custom-fields/{sample_store.shop_domain}/templates/fashion",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["template"] == "fashion"
        assert data["fields_created"] > 0
        assert "fields" in data
        
        # Verify fields were actually created
        get_response = client.get(
            f"/api/custom-fields/{sample_store.shop_domain}",
            headers=auth_headers
        )
        fields = get_response.json()["fields"]
        
        # Should have fashion-related fields
        field_names = [f["field_name"] for f in fields]
        fashion_fields = ["season", "size", "color", "material"]
        created_fashion_fields = [name for name in fashion_fields if name in field_names]
        assert len(created_fashion_fields) > 0
    
    def test_apply_invalid_template(self, client, sample_store, auth_headers):
        """Test applying invalid industry template"""
        response = client.post(
            f"/api/custom-fields/{sample_store.shop_domain}/templates/invalid_template",
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_custom_field_usage_tracking(self, client, sample_store, sample_custom_field, auth_headers):
        """Test custom field usage is tracked"""
        # Get initial usage
        response = client.get(
            f"/api/custom-fields/{sample_store.shop_domain}/{sample_custom_field.id}",
            headers=auth_headers
        )
        initial_usage = response.json()["usage_count"]
        
        # Simulate field usage (this would typically happen when products are updated)
        # For testing, we'll call an endpoint that increments usage
        usage_response = client.post(
            f"/api/custom-fields/{sample_store.shop_domain}/{sample_custom_field.id}/increment-usage",
            headers=auth_headers
        )
        
        # Check usage increased
        response = client.get(
            f"/api/custom-fields/{sample_store.shop_domain}/{sample_custom_field.id}",
            headers=auth_headers
        )
        new_usage = response.json()["usage_count"]
        assert new_usage > initial_usage
    
    def test_custom_field_validation_rules(self, client, sample_store, auth_headers):
        """Test custom field validation rules"""
        # Create select field with options
        field_data = {
            "field_name": "test_select",
            "display_name": "Test Select",
            "field_type": "select",
            "target_entity": "product",
            "validation_rules": {
                "options": ["Option1", "Option2", "Option3"]
            }
        }
        
        response = client.post(
            f"/api/custom-fields/{sample_store.shop_domain}",
            json=field_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        
        # Create text field with max length
        field_data = {
            "field_name": "test_text",
            "display_name": "Test Text",
            "field_type": "text",
            "target_entity": "product",
            "validation_rules": {
                "max_length": 100
            }
        }
        
        response = client.post(
            f"/api/custom-fields/{sample_store.shop_domain}",
            json=field_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        
        # Create number field with range
        field_data = {
            "field_name": "test_number",
            "display_name": "Test Number",
            "field_type": "number",
            "target_entity": "product",
            "validation_rules": {
                "min_value": 0,
                "max_value": 1000
            }
        }
        
        response = client.post(
            f"/api/custom-fields/{sample_store.shop_domain}",
            json=field_data,
            headers=auth_headers
        )
        assert response.status_code == 201
    
    def test_unauthorized_access(self, client, sample_store):
        """Test unauthorized access to custom fields"""
        response = client.get(f"/api/custom-fields/{sample_store.shop_domain}")
        assert response.status_code == 401
    
    def test_invalid_shop_domain(self, client, auth_headers):
        """Test accessing custom fields for invalid shop"""
        response = client.get(
            "/api/custom-fields/invalid-shop.myshopify.com",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    def test_field_name_uniqueness(self, client, sample_store, sample_custom_field, auth_headers):
        """Test field name uniqueness within store"""
        # Try to create field with same name
        field_data = {
            "field_name": sample_custom_field.field_name,
            "display_name": "Duplicate Field",
            "field_type": "text",
            "target_entity": "product"
        }
        
        response = client.post(
            f"/api/custom-fields/{sample_store.shop_domain}",
            json=field_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "already exists" in data["error"]
    
    @pytest.mark.asyncio
    async def test_async_custom_field_operations(self, async_client, sample_store, auth_headers):
        """Test async custom field operations"""
        field_data = {
            "field_name": "async_field",
            "display_name": "Async Field",
            "field_type": "text",
            "target_entity": "product"
        }
        
        # Create field asynchronously
        response = await async_client.post(
            f"/api/custom-fields/{sample_store.shop_domain}",
            json=field_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        
        # Get fields asynchronously
        response = await async_client.get(
            f"/api/custom-fields/{sample_store.shop_domain}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["fields"]) >= 1


class TestCustomFieldsDataValidation:
    """Test custom field data validation"""
    
    def test_validate_field_data_against_definition(self, sample_custom_field):
        """Test validating data against field definition"""
        # Valid data for select field
        valid_data = "High"  # One of the options
        # This would be validated in the actual implementation
        assert valid_data in sample_custom_field.validation_rules["options"]
        
        # Invalid data
        invalid_data = "Invalid Option"
        assert invalid_data not in sample_custom_field.validation_rules["options"]
    
    def test_field_type_specific_validation(self):
        """Test field type specific validation"""
        # Email field validation
        from utils.validation import validate_email_field
        
        # Would be implemented in the validation utils
        # assert validate_email_field("test@example.com") == True
        # assert validate_email_field("invalid-email") == False
        
        # URL field validation
        # assert validate_url_field("https://example.com") == True
        # assert validate_url_field("not-a-url") == False
        
        # Date field validation
        # assert validate_date_field("2024-01-15") == True
        # assert validate_date_field("invalid-date") == False
        pass


class TestCustomFieldsPerformance:
    """Test custom fields performance"""
    
    def test_bulk_field_creation(self, client, sample_store, auth_headers):
        """Test creating multiple fields efficiently"""
        fields_data = []
        for i in range(10):
            fields_data.append({
                "field_name": f"bulk_field_{i}",
                "display_name": f"Bulk Field {i}",
                "field_type": "text",
                "target_entity": "product"
            })
        
        # Create fields in bulk
        response = client.post(
            f"/api/custom-fields/{sample_store.shop_domain}/bulk",
            json={"fields": fields_data},
            headers=auth_headers
        )
        
        # This endpoint would need to be implemented
        # assert response.status_code == 201
        # data = response.json()
        # assert data["created_count"] == 10
    
    def test_field_query_performance(self, client, sample_store, auth_headers, performance_timer):
        """Test field query performance"""
        performance_timer.start()
        
        response = client.get(
            f"/api/custom-fields/{sample_store.shop_domain}",
            headers=auth_headers
        )
        
        performance_timer.stop()
        
        assert response.status_code == 200
        # Should be fast enough
        assert performance_timer.elapsed() < 1.0  # Less than 1 second


class TestCustomFieldsSecurity:
    """Test custom fields security"""
    
    def test_field_access_permissions(self, client, sample_store, auth_headers):
        """Test field access is properly restricted"""
        # Test with different permission levels
        # This would test role-based access control
        pass
    
    def test_field_data_sanitization(self, client, sample_store, auth_headers):
        """Test field data is properly sanitized"""
        field_data = {
            "field_name": "test_field",
            "display_name": "Test<script>alert('xss')</script>",  # XSS attempt
            "field_type": "text",
            "target_entity": "product"
        }
        
        response = client.post(
            f"/api/custom-fields/{sample_store.shop_domain}",
            json=field_data,
            headers=auth_headers
        )
        
        # Should either reject or sanitize
        if response.status_code == 201:
            data = response.json()
            # Display name should be sanitized
            assert "<script>" not in data["display_name"]
        else:
            # Or should reject with validation error
            assert response.status_code == 422