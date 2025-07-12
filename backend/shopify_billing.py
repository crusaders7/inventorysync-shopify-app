"""
Shopify Billing API Integration
Handles recurring charges and subscription management
"""

import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from config import settings

logger = logging.getLogger(__name__)


class ShopifyBillingClient:
    """Client for Shopify Billing API operations"""
    
    def __init__(self, shop_domain: str, access_token: str):
        self.shop_domain = shop_domain
        self.access_token = access_token
        self.base_url = f"https://{shop_domain}/admin/api/2024-01/recurring_application_charges"
        self.headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }
    
    async def create_recurring_charge(
        self, 
        plan_name: str, 
        price: float, 
        trial_days: int = 7,
        return_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a recurring application charge"""
        
        if not return_url:
            return_url = f"{settings.app_url}/api/v1/billing/callback"
        
        charge_data = {
            "recurring_application_charge": {
                "name": plan_name,
                "price": price,
                "trial_days": trial_days,
                "test": not settings.environment == "production",
                "return_url": return_url
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url + ".json",
                    headers=self.headers,
                    json=charge_data,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(
                    f"Created recurring charge",
                    shop_domain=self.shop_domain,
                    charge_id=result["recurring_application_charge"]["id"],
                    plan=plan_name,
                    price=price
                )
                
                return result["recurring_application_charge"]
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to create recurring charge: {e}")
            raise Exception(f"Billing API error: {str(e)}")
    
    async def activate_charge(self, charge_id: str) -> Dict[str, Any]:
        """Activate a recurring charge after merchant approval"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/{charge_id}/activate.json",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(
                    f"Activated recurring charge",
                    shop_domain=self.shop_domain,
                    charge_id=charge_id
                )
                
                return result["recurring_application_charge"]
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to activate charge: {e}")
            raise Exception(f"Billing activation error: {str(e)}")
    
    async def get_charge(self, charge_id: str) -> Dict[str, Any]:
        """Get details of a specific recurring charge"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/{charge_id}.json",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                return response.json()["recurring_application_charge"]
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to get charge: {e}")
            raise Exception(f"Billing API error: {str(e)}")
    
    async def cancel_charge(self, charge_id: str) -> bool:
        """Cancel a recurring charge"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/{charge_id}.json",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                logger.info(
                    f"Cancelled recurring charge",
                    shop_domain=self.shop_domain,
                    charge_id=charge_id
                )
                
                return True
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to cancel charge: {e}")
            return False
    
    async def create_usage_charge(
        self, 
        recurring_charge_id: str, 
        description: str, 
        price: float
    ) -> Dict[str, Any]:
        """Create a usage charge for additional features"""
        
        usage_data = {
            "usage_charge": {
                "description": description,
                "price": price
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/{recurring_charge_id}/usage_charges.json",
                    headers=self.headers,
                    json=usage_data,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(
                    f"Created usage charge",
                    shop_domain=self.shop_domain,
                    recurring_charge_id=recurring_charge_id,
                    description=description,
                    price=price
                )
                
                return result["usage_charge"]
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to create usage charge: {e}")
            raise Exception(f"Usage charge error: {str(e)}")


class BillingPlanManager:
    """Manages subscription plans and pricing"""
    
    PLANS = {
        "starter": {
            "name": "FlexInventory Starter",
            "price": 49.0,
            "features": [
                "Up to 1,000 products",
                "5 custom fields per product",
                "Basic alerts",
                "Email support"
            ],
            "limits": {
                "products": 1000,
                "custom_fields": 5,
                "locations": 1,
                "workflows": 3
            }
        },
        "growth": {
            "name": "FlexInventory Growth", 
            "price": 149.0,
            "features": [
                "Up to 10,000 products",
                "Unlimited custom fields",
                "Advanced workflows",
                "Custom alerts",
                "Multi-location support",
                "Industry templates",
                "Priority support"
            ],
            "limits": {
                "products": 10000,
                "custom_fields": -1,  # unlimited
                "locations": 10,
                "workflows": -1
            }
        },
        "pro": {
            "name": "FlexInventory Pro",
            "price": 299.0,
            "features": [
                "Unlimited products",
                "Unlimited custom fields",
                "Advanced workflows & automation",
                "Custom integrations API",
                "White-label reporting",
                "Multi-channel sync",
                "24/7 phone support"
            ],
            "limits": {
                "products": -1,
                "custom_fields": -1,
                "locations": -1,
                "workflows": -1
            }
        }
    }
    
    @classmethod
    def get_plan_details(cls, plan_name: str) -> Dict[str, Any]:
        """Get plan configuration"""
        return cls.PLANS.get(plan_name, cls.PLANS["starter"])
    
    @classmethod
    def check_feature_limit(cls, plan_name: str, feature: str, current_count: int) -> bool:
        """Check if feature usage is within plan limits"""
        plan = cls.get_plan_details(plan_name)
        limit = plan["limits"].get(feature, 0)
        
        # -1 means unlimited
        if limit == -1:
            return True
        
        return current_count < limit
    
    @classmethod
    def get_upgrade_recommendation(cls, plan_name: str, usage: Dict[str, int]) -> Optional[str]:
        """Recommend plan upgrade based on usage"""
        current_plan = cls.get_plan_details(plan_name)
        
        for feature, count in usage.items():
            limit = current_plan["limits"].get(feature, 0)
            if limit != -1 and count >= limit * 0.9:  # 90% usage threshold
                # Find next plan that supports this usage
                for plan_key in ["starter", "growth", "pro"]:
                    if plan_key == plan_name:
                        continue
                    plan = cls.get_plan_details(plan_key)
                    if plan["limits"].get(feature, 0) == -1 or plan["limits"].get(feature, 0) > count:
                        return plan_key
        
        return None


async def initialize_billing_for_store(shop_domain: str, access_token: str, plan: str = "growth") -> Optional[str]:
    """Initialize billing for a new store installation"""
    
    billing_client = ShopifyBillingClient(shop_domain, access_token)
    plan_details = BillingPlanManager.get_plan_details(plan)
    
    try:
        # Create recurring charge
        charge = await billing_client.create_recurring_charge(
            plan_name=plan_details["name"],
            price=plan_details["price"],
            trial_days=7  # 7-day free trial
        )
        
        # Return confirmation URL for merchant approval
        return charge["confirmation_url"]
        
    except Exception as e:
        logger.error(f"Failed to initialize billing: {e}")
        return None