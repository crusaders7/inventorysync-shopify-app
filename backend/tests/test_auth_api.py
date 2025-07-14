"""
Test suite for Authentication API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import json
import base64
import hmac
import hashlib

from main import app
from models import Store, Location
from config import settings

client = TestClient(app)


class TestAuthAPI:
    """Test cases for authentication endpoints"""

    def test_auth_status_endpoint(self):
        """Test /api/v1/auth/status endpoint"""
        response = client.get("/api/v1/auth/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "configured" in data
        assert "api_key_set" in data
        assert "api_secret_set" in data
        assert "timestamp" in data

    def test_dev_setup_endpoint(self):
        """Test development setup endpoint"""
        shop = "test-dev.myshopify.com"
        
        with patch('api.auth.Store') as mock_store:
            with patch('sqlalchemy.orm.sessionmaker') as mock_sessionmaker:
                mock_session = Mock()
                mock_sessionmaker.return_value = Mock(return_value=mock_session)
                mock_session.query.return_value.filter.return_value.first.return_value = None
                
                response = client.post(f"/api/v1/auth/dev-setup?shop={shop}")
                
                assert response.status_code == 200
                data = response.json()
                assert data["shop"] == shop
                assert "message" in data
                assert "redirect" in data

    def test_install_endpoint_with_valid_shop(self):
        """Test install endpoint with valid shop domain"""
        shop = "valid-store.myshopify.com"
        
        with patch('api.auth.settings') as mock_settings:
            mock_settings.shopify_api_key = "test_api_key_123456789abcdef"
            mock_settings.app_url = "http://localhost:8000"
            
            response = client.get(f"/api/v1/auth/install?shop={shop}")
            
            assert response.status_code == 307  # Redirect
            assert "myshopify.com/admin/oauth/authorize" in response.headers["location"]

    def test_install_endpoint_with_invalid_shop(self):
        """Test install endpoint with invalid shop domain"""
        invalid_shops = [
            "not-a-shop",
            "javascript:alert('xss')",
            "../../etc/passwd",
            "",
            "shop with spaces.myshopify.com"
        ]
        
        for shop in invalid_shops:
            response = client.get(f"/api/v1/auth/install?shop={shop}")
            assert response.status_code in [422, 400]

    @pytest.mark.asyncio
    async def test_callback_endpoint_success(self):
        """Test OAuth callback with successful flow"""
        shop = "test-store.myshopify.com"
        code = "test_auth_code"
        state = "test_state_123"
        
        with patch('api.auth.ShopifyAuth') as mock_auth:
            with patch('api.auth.ShopifyClient') as mock_client:
                with patch('api.auth.AsyncSessionLocal') as mock_session:
                    # Mock the auth exchange
                    mock_auth_instance = AsyncMock()
                    mock_auth.return_value = mock_auth_instance
                    mock_auth_instance.exchange_code_for_token.return_value = "test_access_token"
                    
                    # Mock shop info
                    mock_client_instance = AsyncMock()
                    mock_client.return_value = mock_client_instance
                    mock_client_instance.get_shop_info.return_value = {
                        "shop": {
                            "name": "Test Store",
                            "email": "test@example.com",
                            "currency": "USD",
                            "iana_timezone": "America/New_York"
                        }
                    }
                    mock_client_instance.get_locations.return_value = {
                        "locations": [
                            {
                                "id": "123456",
                                "name": "Main Location",
                                "address1": "123 Main St",
                                "city": "New York",
                                "country_code": "US",
                                "active": True
                            }
                        ]
                    }
                    
                    response = client.get(
                        f"/api/v1/auth/callback?shop={shop}&code={code}&state={state}"
                    )
                    
                    assert response.status_code == 307  # Redirect
                    assert "authenticated=true" in response.headers["location"]

    def test_webhook_endpoint_with_valid_hmac(self):
        """Test webhook endpoint with valid HMAC verification"""
        shop_domain = "test-store.myshopify.com"
        webhook_data = {"id": "12345", "email": "test@example.com"}
        body = json.dumps(webhook_data).encode('utf-8')
        
        # Generate valid HMAC
        secret = "test_webhook_secret"
        calculated_hmac = base64.b64encode(
            hmac.new(
                secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).digest()
        ).decode()
        
        with patch('api.auth.settings') as mock_settings:
            mock_settings.shopify_webhook_secret = secret
            
            response = client.post(
                "/api/v1/auth/webhook",
                headers={
                    "X-Shopify-Topic": "products/create",
                    "X-Shopify-Hmac-Sha256": calculated_hmac,
                    "X-Shopify-Shop-Domain": shop_domain
                },
                content=body
            )
            
            assert response.status_code == 200
            assert response.json()["status"] == "received"

    def test_webhook_endpoint_with_invalid_hmac(self):
        """Test webhook endpoint with invalid HMAC"""
        response = client.post(
            "/api/v1/auth/webhook",
            headers={
                "X-Shopify-Topic": "products/create",
                "X-Shopify-Hmac-Sha256": "invalid_hmac",
                "X-Shopify-Shop-Domain": "test.myshopify.com"
            },
            json={"test": "data"}
        )
        
        assert response.status_code in [400, 401]

    def test_webhook_missing_headers(self):
        """Test webhook endpoint with missing headers"""
        response = client.post(
            "/api/v1/auth/webhook",
            json={"test": "data"}
        )
        
        assert response.status_code == 400

    @pytest.mark.parametrize("topic,handler", [
        ("products/create", "handle_product_created"),
        ("products/update", "handle_product_updated"),
        ("inventory_levels/update", "handle_inventory_updated"),
        ("app/uninstalled", "handle_app_uninstalled"),
        ("customers/data_request", "handle_customer_data_request"),
        ("customers/redact", "handle_customer_redact"),
        ("shop/redact", "handle_shop_redact"),
    ])
    def test_webhook_topics_routing(self, topic, handler):
        """Test that different webhook topics are routed correctly"""
        with patch(f'api.auth.{handler}') as mock_handler:
            with patch('api.auth.settings') as mock_settings:
                mock_settings.shopify_webhook_secret = None  # Disable HMAC for this test
                
                response = client.post(
                    "/api/v1/auth/webhook",
                    headers={
                        "X-Shopify-Topic": topic,
                        "X-Shopify-Hmac-Sha256": "test",
                        "X-Shopify-Shop-Domain": "test.myshopify.com"
                    },
                    json={"test": "data"}
                )
                
                assert response.status_code == 200
                mock_handler.assert_called_once()

    def test_hmac_verification_function(self):
        """Test HMAC verification function"""
        from api.auth import verify_shopify_hmac
        
        api_secret = "test_secret"
        query_params = {
            "shop": "test.myshopify.com",
            "timestamp": "1234567890",
            "hmac": ""
        }
        
        # Generate correct HMAC
        sorted_params = sorted([(k, v) for k, v in query_params.items() if k != 'hmac'])
        query_string = "&".join([f"{k}={v}" for k, v in sorted_params])
        correct_hmac = hmac.new(
            api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        query_params["hmac"] = correct_hmac
        
        # Test with correct HMAC
        assert verify_shopify_hmac(query_params.copy(), api_secret) == True
        
        # Test with incorrect HMAC
        query_params["hmac"] = "incorrect_hmac"
        assert verify_shopify_hmac(query_params.copy(), api_secret) == False


class TestAuthAPIEdgeCases:
    """Test edge cases and error handling"""

    def test_install_with_missing_api_key(self):
        """Test install when API key is not configured"""
        with patch('api.auth.settings') as mock_settings:
            mock_settings.shopify_api_key = None
            
            response = client.get("/api/v1/auth/install?shop=test.myshopify.com")
            assert response.status_code == 500

    def test_callback_with_database_error(self):
        """Test callback handling when database operations fail"""
        with patch('api.auth.AsyncSessionLocal') as mock_session:
            mock_session.side_effect = Exception("Database connection failed")
            
            response = client.get(
                "/api/v1/auth/callback?shop=test.myshopify.com&code=test&state=test"
            )
            
            assert response.status_code == 307  # Still redirects
            assert "error=authentication_failed" in response.headers["location"]

    def test_dev_setup_with_existing_store(self):
        """Test dev setup when store already exists"""
        shop = "existing-dev.myshopify.com"
        
        with patch('sqlalchemy.orm.sessionmaker') as mock_sessionmaker:
            mock_session = Mock()
            mock_sessionmaker.return_value = Mock(return_value=mock_session)
            mock_session.query.return_value.filter.return_value.first.return_value = Mock()  # Existing store
            
            response = client.post(f"/api/v1/auth/dev-setup?shop={shop}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Store already exists"

    @pytest.mark.asyncio
    async def test_setup_mandatory_webhooks(self):
        """Test webhook setup function"""
        from api.auth import setup_mandatory_webhooks
        
        shop_domain = "test.myshopify.com"
        access_token = "test_token"
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "webhook": {"id": "123456", "topic": "app/uninstalled"}
            }
            mock_post.return_value = mock_response
            
            await setup_mandatory_webhooks(shop_domain, access_token)
            
            # Should create 4 mandatory webhooks
            assert mock_post.call_count == 4
            
            # Verify topics
            topics = [
                "app/uninstalled",
                "customers/data_request",
                "customers/redact",
                "shop/redact"
            ]
            for i, call in enumerate(mock_post.call_args_list):
                webhook_data = call[1]["json"]
                assert webhook_data["webhook"]["topic"] in topics
