"""
Billing Plans Configuration
Defines the pricing tiers for InventorySync
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class PlanFeatures:
    """Features included in each plan"""
    stores: int
    products: int
    custom_fields: int
    workflows: int
    locations: int
    users: int
    api_calls: int
    forecasting: bool
    multi_location: bool
    supplier_integration: bool
    priority_support: bool
    custom_reports: bool
    data_export: bool
    advanced_analytics: bool


class BillingPlans:
    """Billing plan definitions"""
    
    PLANS = {
        "starter": {
            "name": "Starter Plan",
            "price": 29.00,
            "trial_days": 14,
            "features": PlanFeatures(
                stores=1,
                products=1000,
                custom_fields=10,
                workflows=5,
                locations=2,
                users=2,
                api_calls=10000,
                forecasting=False,
                multi_location=False,
                supplier_integration=False,
                priority_support=False,
                custom_reports=False,
                data_export=True,
                advanced_analytics=False
            ),
            "description": "Perfect for small businesses just getting started",
            "shopify_plan_id": "starter_plan_2025"
        },
        "growth": {
            "name": "Growth Plan",
            "price": 59.00,
            "trial_days": 14,
            "features": PlanFeatures(
                stores=3,
                products=10000,
                custom_fields=50,
                workflows=20,
                locations=5,
                users=5,
                api_calls=50000,
                forecasting=True,
                multi_location=True,
                supplier_integration=False,
                priority_support=True,
                custom_reports=True,
                data_export=True,
                advanced_analytics=True
            ),
            "description": "Ideal for growing businesses with multiple locations",
            "shopify_plan_id": "growth_plan_2025"
        },
        "pro": {
            "name": "Professional Plan",
            "price": 99.00,
            "trial_days": 14,
            "features": PlanFeatures(
                stores=-1,  # Unlimited
                products=-1,  # Unlimited
                custom_fields=-1,  # Unlimited
                workflows=-1,  # Unlimited
                locations=-1,  # Unlimited
                users=20,
                api_calls=200000,
                forecasting=True,
                multi_location=True,
                supplier_integration=True,
                priority_support=True,
                custom_reports=True,
                data_export=True,
                advanced_analytics=True
            ),
            "description": "Enterprise features at startup prices",
            "shopify_plan_id": "pro_plan_2025"
        },
        "enterprise": {
            "name": "Enterprise Plan",
            "price": 299.00,
            "trial_days": 30,
            "features": PlanFeatures(
                stores=-1,  # Unlimited
                products=-1,  # Unlimited
                custom_fields=-1,  # Unlimited
                workflows=-1,  # Unlimited
                locations=-1,  # Unlimited
                users=-1,  # Unlimited
                api_calls=-1,  # Unlimited
                forecasting=True,
                multi_location=True,
                supplier_integration=True,
                priority_support=True,
                custom_reports=True,
                data_export=True,
                advanced_analytics=True
            ),
            "description": "White-glove service for large operations",
            "shopify_plan_id": "enterprise_plan_2025",
            "custom_features": [
                "Dedicated account manager",
                "Custom integrations",
                "SLA guarantee",
                "Training sessions",
                "API priority access"
            ]
        }
    }
    
    @classmethod
    def get_plan(cls, plan_name: str) -> Dict[str, Any]:
        """Get plan details by name"""
        return cls.PLANS.get(plan_name.lower())
    
    @classmethod
    def get_features(cls, plan_name: str) -> PlanFeatures:
        """Get plan features"""
        plan = cls.get_plan(plan_name)
        return plan["features"] if plan else None
    
    @classmethod
    def check_limit(cls, plan_name: str, feature: str, current_value: int) -> bool:
        """Check if a feature limit has been reached"""
        features = cls.get_features(plan_name)
        if not features:
            return False
        
        limit = getattr(features, feature, 0)
        if limit == -1:  # Unlimited
            return True
        
        return current_value < limit
    
    @classmethod
    def get_usage_percentage(cls, plan_name: str, feature: str, current_value: int) -> float:
        """Get usage percentage for a feature"""
        features = cls.get_features(plan_name)
        if not features:
            return 0.0
        
        limit = getattr(features, feature, 0)
        if limit == -1:  # Unlimited
            return 0.0
        
        return (current_value / limit) * 100 if limit > 0 else 100.0


# Export for backward compatibility
BILLING_PLANS = BillingPlans.PLANS