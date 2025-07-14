"""
Test suite for Shopify Billing Client
"""
import pytest
from unittest.mock import patch, AsyncMock
from shopify_billing import ShopifyBillingClient, BillingPlanManager
import httpx

@pytest.mark.asyncio
async def test_create_recurring_charge_success():
    """Test successful creation of a recurring charge"""
    shop_domain = "test-shop.myshopify.com"
    access_token = "dummy_access_token"
    plan_name = "Test Plan"
    price = 19.99

    billing_client = ShopifyBillingClient(shop_domain, access_token)
    charge_response = {
        "recurring_application_charge": {
            "id": "123456789",
            "name": plan_name,
            "return_url": "http://example.com",
            "price": price
        }
    }

    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value.__aenter__.return_value.json = AsyncMock(return_value=charge_response)
        mock_post.return_value.__aenter__.return_value.status_code = 201
        
        charge = await billing_client.create_recurring_charge(plan_name, price)
        assert charge["id"] == "123456789"

@pytest.mark.asyncio
async def test_create_recurring_charge_failure():
    """Test failed creation of a recurring charge due to API error"""
    shop_domain = "error-shop.myshopify.com"
    access_token = "dummy_access_token"

    billing_client = ShopifyBillingClient(shop_domain, access_token)

    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value.__aenter__.return_value.raise_for_status.side_effect = Exception("API error")

        with pytest.raises(Exception) as excinfo:
            await billing_client.create_recurring_charge("Error Plan", 99.99)
        assert "Billing API error" in str(excinfo.value)

@pytest.mark.asyncio
async def test_cancel_charge_success():
    """Test successful cancellation of a charge"""
    shop_domain = "cancel-shop.myshopify.com"
    access_token = "dummy_access_token"
    charge_id = "987654321"

    billing_client = ShopifyBillingClient(shop_domain, access_token)

    with patch('httpx.AsyncClient.delete') as mock_delete:
        mock_delete.return_value.__aenter__.return_value.status_code = 200
        
        success = await billing_client.cancel_charge(charge_id)
        assert success

@pytest.mark.asyncio
async def test_billing_plan_manager_limits():
    """Test the feature limit checks of BillingPlanManager"""
    assert BillingPlanManager.check_feature_limit("unlimited", "products", 1000)
    assert BillingPlanManager.check_feature_limit("unlimited", "custom_fields", -1)

@pytest.mark.asyncio
async def test_upgrade_recommendation():
    """Test the upgrade recommendation logic"""
    usage = {"products": 5000}
    recommendation = BillingPlanManager.get_upgrade_recommendation("unlimited", usage)
    assert recommendation is None
