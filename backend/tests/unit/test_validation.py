"""
Unit tests for validation utilities
Tests all validation classes and security features
"""

import pytest
from datetime import datetime
from utils.validation import (
    ShopDomainValidator,
    SKUValidator,
    StockValidator,
    ProductValidator,
    AlertValidator,
    APIKeyValidator,
    EnhancedShopifyValidator,
    CustomFieldValidator,
    WorkflowValidator,
    SecurityValidator,
    RateLimitValidator,
    ValidationError,
    validate_request_data,
    sanitize_string,
    validate_pagination,
    validate_sort_params,
    validate_json_structure
)
from fastapi import HTTPException


class TestShopDomainValidator:
    """Test basic shop domain validation"""
    
    def test_valid_domain(self):
        """Test valid shop domain formats"""
        assert ShopDomainValidator.validate("test-store.myshopify.com") == "test-store.myshopify.com"
        assert ShopDomainValidator.validate("my-awesome-store.myshopify.com") == "my-awesome-store.myshopify.com"
    
    def test_domain_without_suffix(self):
        """Test domain without .myshopify.com suffix gets corrected"""
        assert ShopDomainValidator.validate("test-store") == "test-store.myshopify.com"
        assert ShopDomainValidator.validate("my-store") == "my-store.myshopify.com"
    
    def test_domain_with_protocol(self):
        """Test domain with protocol gets cleaned"""
        assert ShopDomainValidator.validate("https://test-store.myshopify.com") == "test-store.myshopify.com"
        assert ShopDomainValidator.validate("http://test-store.myshopify.com") == "test-store.myshopify.com"
    
    def test_empty_domain(self):
        """Test empty domain raises error"""
        with pytest.raises(ValueError, match="Shop domain is required"):
            ShopDomainValidator.validate("")
        
        with pytest.raises(ValueError, match="Shop domain is required"):
            ShopDomainValidator.validate(None)
    
    def test_invalid_domain_format(self):
        """Test invalid domain formats"""
        with pytest.raises(ValueError, match="Invalid shop domain format"):
            ShopDomainValidator.validate("test-store.com")
        
        with pytest.raises(ValueError, match="Shop name must be 3-60 characters"):
            ShopDomainValidator.validate("ab.myshopify.com")
    
    def test_shop_name_validation(self):
        """Test shop name character validation"""
        # Valid characters
        assert ShopDomainValidator.validate("test123-store") == "test123-store.myshopify.com"
        
        # Invalid characters
        with pytest.raises(ValueError, match="contain only lowercase letters"):
            ShopDomainValidator.validate("Test_Store")  # uppercase and underscore


class TestSKUValidator:
    """Test SKU validation"""
    
    def test_valid_sku(self):
        """Test valid SKU formats"""
        assert SKUValidator.validate("TEST-SKU-001") == "TEST-SKU-001"
        assert SKUValidator.validate("PRODUCT_123") == "PRODUCT_123"
        assert SKUValidator.validate("ABC123XYZ") == "ABC123XYZ"
    
    def test_sku_normalization(self):
        """Test SKU gets normalized to uppercase"""
        assert SKUValidator.validate("test-sku-001") == "TEST-SKU-001"
        assert SKUValidator.validate("  product_123  ") == "PRODUCT_123"
    
    def test_empty_sku(self):
        """Test empty SKU raises error"""
        with pytest.raises(ValueError, match="SKU is required"):
            SKUValidator.validate("")
        
        with pytest.raises(ValueError, match="SKU is required"):
            SKUValidator.validate(None)
    
    def test_sku_length_validation(self):
        """Test SKU length limits"""
        # Too short
        with pytest.raises(ValueError, match="SKU must be between 2 and 50 characters"):
            SKUValidator.validate("A")
        
        # Too long
        with pytest.raises(ValueError, match="SKU must be between 2 and 50 characters"):
            SKUValidator.validate("A" * 51)
    
    def test_sku_character_validation(self):
        """Test SKU character restrictions"""
        # Valid characters
        assert SKUValidator.validate("ABC-123_XYZ") == "ABC-123_XYZ"
        
        # Invalid characters
        with pytest.raises(ValueError, match="can only contain uppercase letters"):
            SKUValidator.validate("SKU@123")
        
        with pytest.raises(ValueError, match="can only contain uppercase letters"):
            SKUValidator.validate("SKU 123")  # space


class TestStockValidator:
    """Test stock quantity validation"""
    
    def test_valid_quantity(self):
        """Test valid stock quantities"""
        assert StockValidator.validate_quantity(0) == 0
        assert StockValidator.validate_quantity(100) == 100
        assert StockValidator.validate_quantity(999999) == 999999
    
    def test_invalid_quantity_type(self):
        """Test non-integer quantities"""
        with pytest.raises(ValueError, match="Quantity must be an integer"):
            StockValidator.validate_quantity("100")
        
        with pytest.raises(ValueError, match="Quantity must be an integer"):
            StockValidator.validate_quantity(100.5)
    
    def test_negative_quantity(self):
        """Test negative quantities"""
        with pytest.raises(ValueError, match="Quantity cannot be negative"):
            StockValidator.validate_quantity(-1)
    
    def test_quantity_upper_limit(self):
        """Test quantity upper limits"""
        with pytest.raises(ValueError, match="Quantity cannot exceed 1,000,000"):
            StockValidator.validate_quantity(1000001)
    
    def test_valid_reorder_point(self):
        """Test valid reorder points"""
        assert StockValidator.validate_reorder_point(0) == 0
        assert StockValidator.validate_reorder_point(50) == 50
        assert StockValidator.validate_reorder_point(99999) == 99999
    
    def test_reorder_point_limits(self):
        """Test reorder point limits"""
        with pytest.raises(ValueError, match="Reorder point cannot exceed 100,000"):
            StockValidator.validate_reorder_point(100001)


class TestEnhancedShopifyValidator:
    """Test enhanced Shopify domain validation with security"""
    
    def test_valid_domain_validation(self):
        """Test valid domain validation"""
        domain = EnhancedShopifyValidator.validate_domain("test-store.myshopify.com")
        assert domain == "test-store.myshopify.com"
    
    def test_domain_normalization(self):
        """Test domain normalization"""
        domain = EnhancedShopifyValidator.validate_domain("Test-Store.MyShopify.Com")
        assert domain == "test-store.myshopify.com"
    
    def test_blocked_domains(self):
        """Test blocked domain names"""
        for blocked_name in ["test", "demo", "admin", "api", "staging"]:
            with pytest.raises(ValidationError, match="reserved domain name"):
                EnhancedShopifyValidator.validate_domain(f"{blocked_name}.myshopify.com")
    
    def test_invalid_domain_patterns(self):
        """Test invalid domain patterns"""
        # Double hyphens
        with pytest.raises(ValidationError, match="Invalid shop name format"):
            EnhancedShopifyValidator.validate_domain("test--store.myshopify.com")
        
        # Starting with hyphen
        with pytest.raises(ValidationError, match="Invalid shop name format"):
            EnhancedShopifyValidator.validate_domain("-test-store.myshopify.com")
        
        # Ending with hyphen
        with pytest.raises(ValidationError, match="Invalid shop name format"):
            EnhancedShopifyValidator.validate_domain("test-store-.myshopify.com")
    
    def test_shop_name_too_short(self):
        """Test shop name minimum length"""
        with pytest.raises(ValidationError, match="Shop name too short"):
            EnhancedShopifyValidator.validate_domain("ab.myshopify.com")


class TestCustomFieldValidator:
    """Test custom field validation"""
    
    def test_valid_field_definition(self):
        """Test valid custom field definition"""
        field_data = {
            "field_name": "priority",
            "display_name": "Product Priority",
            "field_type": "select",
            "target_entity": "product",
            "validation_rules": {"options": ["Low", "Medium", "High"]},
            "is_required": False
        }
        
        result = CustomFieldValidator.validate_field_definition(field_data)
        assert result["field_name"] == "priority"
    
    def test_field_name_validation(self):
        """Test field name validation"""
        field_data = {
            "field_name": "Priority",  # Invalid: uppercase
            "display_name": "Product Priority",
            "field_type": "text",
            "target_entity": "product"
        }
        
        with pytest.raises(ValidationError, match="must start with letter"):
            CustomFieldValidator.validate_field_definition(field_data)
    
    def test_reserved_field_names(self):
        """Test reserved field names"""
        for reserved_name in ["id", "created_at", "password", "token"]:
            field_data = {
                "field_name": reserved_name,
                "display_name": "Test Field",
                "field_type": "text",
                "target_entity": "product"
            }
            
            with pytest.raises(ValidationError, match="reserved name"):
                CustomFieldValidator.validate_field_definition(field_data)
    
    def test_invalid_field_type(self):
        """Test invalid field type"""
        field_data = {
            "field_name": "test_field",
            "display_name": "Test Field",
            "field_type": "invalid_type",
            "target_entity": "product"
        }
        
        with pytest.raises(ValidationError, match="Invalid field type"):
            CustomFieldValidator.validate_field_definition(field_data)
    
    def test_select_field_validation(self):
        """Test select field validation rules"""
        # Valid select field
        field_data = {
            "field_name": "priority",
            "display_name": "Priority",
            "field_type": "select",
            "target_entity": "product",
            "validation_rules": {"options": ["Low", "Medium", "High"]}
        }
        
        result = CustomFieldValidator.validate_field_definition(field_data)
        assert result["field_name"] == "priority"
        
        # Too many options
        field_data["validation_rules"]["options"] = ["Option" + str(i) for i in range(101)]
        with pytest.raises(ValidationError, match="Too many options"):
            CustomFieldValidator.validate_field_definition(field_data)


class TestWorkflowValidator:
    """Test workflow rule validation"""
    
    def test_valid_workflow_rule(self):
        """Test valid workflow rule"""
        rule_data = {
            "rule_name": "Low Stock Alert",
            "trigger_event": "inventory_low",
            "trigger_conditions": {
                "field": "current_stock",
                "operator": "less_than",
                "value": 10
            },
            "actions": [
                {
                    "type": "create_alert",
                    "title": "Low Stock",
                    "message": "Stock is low",
                    "severity": "high"
                }
            ]
        }
        
        result = WorkflowValidator.validate_workflow_rule(rule_data)
        assert result["rule_name"] == "Low Stock Alert"
    
    def test_invalid_trigger_event(self):
        """Test invalid trigger event"""
        rule_data = {
            "rule_name": "Test Rule",
            "trigger_event": "invalid_event",
            "actions": [{"type": "create_alert", "message": "Test"}]
        }
        
        with pytest.raises(ValidationError, match="Invalid trigger event"):
            WorkflowValidator.validate_workflow_rule(rule_data)
    
    def test_webhook_url_validation(self):
        """Test webhook URL security validation"""
        rule_data = {
            "rule_name": "Webhook Rule",
            "trigger_event": "inventory_low",
            "actions": [
                {
                    "type": "send_webhook",
                    "url": "http://localhost:8080/webhook"  # Blocked internal URL
                }
            ]
        }
        
        with pytest.raises(ValidationError, match="cannot point to internal networks"):
            WorkflowValidator.validate_workflow_rule(rule_data)
    
    def test_complex_conditions_validation(self):
        """Test complex nested conditions"""
        rule_data = {
            "rule_name": "Complex Rule",
            "trigger_event": "inventory_low",
            "trigger_conditions": {
                "type": "and",
                "conditions": [
                    {"field": "current_stock", "operator": "less_than", "value": 10},
                    {
                        "type": "or",
                        "conditions": [
                            {"field": "priority", "operator": "equals", "value": "high"},
                            {"field": "cost", "operator": "greater_than", "value": 100}
                        ]
                    }
                ]
            },
            "actions": [{"type": "create_alert", "message": "Test"}]
        }
        
        result = WorkflowValidator.validate_workflow_rule(rule_data)
        assert result["rule_name"] == "Complex Rule"


class TestSecurityValidator:
    """Test security validation utilities"""
    
    def test_input_sanitization(self):
        """Test input sanitization"""
        # Clean input
        clean = SecurityValidator.sanitize_input("Hello World")
        assert clean == "Hello World"
        
        # Input with null bytes
        dirty = SecurityValidator.sanitize_input("Hello\x00World")
        assert "\x00" not in dirty
        
        # XSS attempt
        with pytest.raises(ValidationError, match="potentially unsafe content"):
            SecurityValidator.sanitize_input("<script>alert('xss')</script>")
        
        # JavaScript protocol
        with pytest.raises(ValidationError, match="potentially unsafe content"):
            SecurityValidator.sanitize_input("javascript:alert('xss')")
    
    def test_api_key_validation(self):
        """Test API key format validation"""
        # Valid API key
        valid_key = SecurityValidator.validate_api_key_format("isk_AbCdEf123456789")
        assert valid_key == "isk_AbCdEf123456789"
        
        # Invalid prefix
        with pytest.raises(ValidationError, match="Invalid API key format"):
            SecurityValidator.validate_api_key_format("invalid_key")
        
        # Too short
        with pytest.raises(ValidationError, match="Invalid API key length"):
            SecurityValidator.validate_api_key_format("isk_short")
        
        # Invalid characters
        with pytest.raises(ValidationError, match="API key contains invalid characters"):
            SecurityValidator.validate_api_key_format("isk_invalid@characters!")


class TestRateLimitValidator:
    """Test rate limiting validation"""
    
    def test_rate_limit_validation(self):
        """Test rate limit checking"""
        # Within limits
        assert RateLimitValidator.validate_rate_limit("api_requests", 500) == True
        
        # Exceeds limit
        with pytest.raises(ValidationError, match="Rate limit exceeded"):
            RateLimitValidator.validate_rate_limit("api_requests", 1001)
    
    def test_custom_rate_limits(self):
        """Test custom rate limits"""
        # Custom limit
        assert RateLimitValidator.validate_rate_limit("custom_operation", 50, limit=100) == True
        
        # Exceeds custom limit
        with pytest.raises(ValidationError, match="Rate limit exceeded"):
            RateLimitValidator.validate_rate_limit("custom_operation", 101, limit=100)


class TestUtilityFunctions:
    """Test utility validation functions"""
    
    def test_validate_request_data(self):
        """Test request data validation"""
        data = {"field1": "value1", "field2": "value2"}
        required = ["field1", "field2"]
        
        result = validate_request_data(data, required)
        assert result == data
        
        # Missing required fields
        with pytest.raises(HTTPException) as exc_info:
            validate_request_data({"field1": "value1"}, required)
        assert exc_info.value.status_code == 422
    
    def test_sanitize_string(self):
        """Test string sanitization"""
        # Normal string
        assert sanitize_string("Hello World") == "Hello World"
        
        # String with dangerous characters
        dirty = "Hello<script>World"
        clean = sanitize_string(dirty)
        assert "<" not in clean and ">" not in clean
        
        # Length limit
        long_string = "A" * 1000
        short = sanitize_string(long_string, max_length=10)
        assert len(short) == 10
    
    def test_validate_pagination(self):
        """Test pagination validation"""
        # Valid pagination
        page, limit = validate_pagination(1, 20)
        assert page == 1 and limit == 20
        
        # Invalid page
        with pytest.raises(Exception):  # Should raise validation_error
            validate_pagination(0, 20)
        
        # Invalid limit
        with pytest.raises(Exception):  # Should raise validation_error
            validate_pagination(1, 101)
    
    def test_validate_sort_params(self):
        """Test sort parameter validation"""
        # Valid sort
        field, order = validate_sort_params("id", "asc")
        assert field == "id" and order == "asc"
        
        # Case insensitive order
        field, order = validate_sort_params("id", "DESC")
        assert order == "desc"
        
        # Invalid field
        with pytest.raises(Exception):  # Should raise validation_error
            validate_sort_params("invalid_field", "asc")
    
    def test_validate_json_structure(self):
        """Test JSON structure validation"""
        # Valid JSON
        data = {"key1": "value1", "nested": {"key2": "value2"}}
        result = validate_json_structure(data)
        assert result == data
        
        # Too deeply nested
        deeply_nested = {"level1": {"level2": {"level3": {"level4": {}}}}}
        for i in range(10):  # Create deep nesting
            deeply_nested = {"level": deeply_nested}
        
        with pytest.raises(ValidationError, match="too deeply nested"):
            validate_json_structure(deeply_nested, max_depth=5)
        
        # Too many keys
        too_many_keys = {f"key{i}": f"value{i}" for i in range(101)}
        with pytest.raises(ValidationError, match="Too many keys"):
            validate_json_structure(too_many_keys, max_keys=100)
        
        # Array too large
        large_array = list(range(1001))
        with pytest.raises(ValidationError, match="Array too large"):
            validate_json_structure(large_array)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestValidationIntegration:
    """Test validation integration scenarios"""
    
    def test_shopify_domain_to_custom_field_flow(self):
        """Test complete validation flow from domain to custom field"""
        # Step 1: Validate shop domain
        domain = EnhancedShopifyValidator.validate_domain("test-store.myshopify.com")
        assert domain == "test-store.myshopify.com"
        
        # Step 2: Create custom field for this store
        field_data = {
            "field_name": "category",
            "display_name": "Product Category",
            "field_type": "select",
            "target_entity": "product",
            "validation_rules": {"options": ["Electronics", "Clothing", "Home"]}
        }
        
        validated_field = CustomFieldValidator.validate_field_definition(field_data)
        assert validated_field["field_name"] == "category"
        
        # Step 3: Validate workflow rule using this field
        rule_data = {
            "rule_name": "Category Alert",
            "trigger_event": "custom_field_change",
            "trigger_conditions": {
                "field": "category",
                "operator": "equals",
                "value": "Electronics"
            },
            "actions": [
                {
                    "type": "create_alert",
                    "title": "Electronics Product Updated",
                    "message": "Electronics product modified",
                    "severity": "info"
                }
            ]
        }
        
        validated_rule = WorkflowValidator.validate_workflow_rule(rule_data)
        assert validated_rule["rule_name"] == "Category Alert"
    
    def test_security_validation_chain(self):
        """Test security validation across multiple components"""
        # Sanitize input
        user_input = "Product Name <script>alert('test')</script>"
        try:
            clean_input = SecurityValidator.sanitize_input(user_input)
            assert False, "Should have raised ValidationError"
        except ValidationError:
            pass  # Expected
        
        # Use safe input instead
        safe_input = SecurityValidator.sanitize_input("Product Name")
        assert safe_input == "Product Name"
        
        # Validate API key
        api_key = SecurityValidator.validate_api_key_format("isk_AbCdEf123456789_ValidKey")
        assert api_key.startswith("isk_")
        
        # Check rate limits
        assert RateLimitValidator.validate_rate_limit("api_requests", 100) == True