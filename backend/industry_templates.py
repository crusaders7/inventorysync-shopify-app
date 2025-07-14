"""
Industry Templates for Custom Fields
Pre-configured field sets for different business types
"""

from typing import Dict, List, Any
from datetime import datetime


class IndustryTemplates:
    """Pre-built templates for various industries"""
    
    TEMPLATES = {
        "apparel": {
            "name": "Apparel & Fashion",
            "description": "Track sizes, colors, seasons, and materials",
            "custom_fields": [
                {
                    "field_name": "size",
                    "display_name": "Size",
                    "field_type": "select",
                    "validation_rules": {
                        "options": ["XS", "S", "M", "L", "XL", "XXL", "XXXL"]
                    },
                    "is_required": True,
                    "is_filterable": True
                },
                {
                    "field_name": "color",
                    "display_name": "Color",
                    "field_type": "text",
                    "is_required": True,
                    "is_filterable": True
                },
                {
                    "field_name": "material",
                    "display_name": "Material Composition",
                    "field_type": "textarea",
                    "help_text": "e.g., 80% Cotton, 20% Polyester"
                },
                {
                    "field_name": "season",
                    "display_name": "Season",
                    "field_type": "select",
                    "validation_rules": {
                        "options": ["Spring", "Summer", "Fall", "Winter", "All-Season"]
                    },
                    "is_filterable": True
                },
                {
                    "field_name": "care_instructions",
                    "display_name": "Care Instructions",
                    "field_type": "textarea"
                }
            ],
            "workflows": [
                {
                    "name": "Low Stock Alert by Size",
                    "trigger": "inventory_level_low",
                    "conditions": {
                        "inventory_level": "< 5",
                        "custom_fields.size": "exists"
                    },
                    "actions": ["send_email", "create_reorder_suggestion"]
                }
            ]
        },
        
        "electronics": {
            "name": "Electronics & Tech",
            "description": "Manage warranties, specifications, and compatibility",
            "custom_fields": [
                {
                    "field_name": "warranty_months",
                    "display_name": "Warranty Period (Months)",
                    "field_type": "number",
                    "validation_rules": {
                        "min": 0,
                        "max": 60
                    },
                    "is_required": True
                },
                {
                    "field_name": "serial_number_prefix",
                    "display_name": "Serial Number Prefix",
                    "field_type": "text",
                    "help_text": "Prefix for batch tracking"
                },
                {
                    "field_name": "compatibility",
                    "display_name": "Compatible With",
                    "field_type": "multi_select",
                    "validation_rules": {
                        "options": ["Windows", "Mac", "Linux", "iOS", "Android", "Universal"]
                    }
                },
                {
                    "field_name": "power_requirements",
                    "display_name": "Power Requirements",
                    "field_type": "text",
                    "help_text": "e.g., 110-240V, 50/60Hz"
                },
                {
                    "field_name": "certification",
                    "display_name": "Certifications",
                    "field_type": "multi_select",
                    "validation_rules": {
                        "options": ["CE", "FCC", "RoHS", "UL", "Energy Star"]
                    }
                }
            ],
            "workflows": [
                {
                    "name": "Warranty Expiration Alert",
                    "trigger": "daily_check",
                    "conditions": {
                        "warranty_expiry": "< 30 days"
                    },
                    "actions": ["notify_customer", "create_task"]
                }
            ]
        },
        
        "food_beverage": {
            "name": "Food & Beverage",
            "description": "Track expiration dates, batches, and storage requirements",
            "custom_fields": [
                {
                    "field_name": "expiration_date",
                    "display_name": "Expiration Date",
                    "field_type": "date",
                    "is_required": True,
                    "is_filterable": True
                },
                {
                    "field_name": "batch_number",
                    "display_name": "Batch/Lot Number",
                    "field_type": "text",
                    "is_required": True,
                    "is_searchable": True
                },
                {
                    "field_name": "storage_temp",
                    "display_name": "Storage Temperature",
                    "field_type": "select",
                    "validation_rules": {
                        "options": ["Frozen (-18°C)", "Refrigerated (2-8°C)", "Cool (8-15°C)", "Room Temperature"]
                    }
                },
                {
                    "field_name": "allergens",
                    "display_name": "Contains Allergens",
                    "field_type": "multi_select",
                    "validation_rules": {
                        "options": ["Gluten", "Dairy", "Eggs", "Soy", "Nuts", "Shellfish", "None"]
                    }
                },
                {
                    "field_name": "organic_certified",
                    "display_name": "Organic Certified",
                    "field_type": "boolean",
                    "default_value": "false"
                }
            ],
            "workflows": [
                {
                    "name": "Expiration Alert",
                    "trigger": "daily_check",
                    "conditions": {
                        "days_until_expiry": "< 30"
                    },
                    "actions": ["send_alert", "flag_for_discount", "prevent_reorder"]
                },
                {
                    "name": "FIFO Enforcement",
                    "trigger": "order_fulfillment",
                    "conditions": {
                        "has_expiration": "true"
                    },
                    "actions": ["select_oldest_batch"]
                }
            ]
        },
        
        "jewelry": {
            "name": "Jewelry & Accessories",
            "description": "Manage precious metals, stones, and certifications",
            "custom_fields": [
                {
                    "field_name": "metal_type",
                    "display_name": "Metal Type",
                    "field_type": "select",
                    "validation_rules": {
                        "options": ["Gold 14K", "Gold 18K", "Gold 24K", "Silver 925", "Platinum", "Stainless Steel", "Other"]
                    },
                    "is_filterable": True
                },
                {
                    "field_name": "stone_type",
                    "display_name": "Primary Stone",
                    "field_type": "text",
                    "help_text": "e.g., Diamond, Ruby, Sapphire"
                },
                {
                    "field_name": "carat_weight",
                    "display_name": "Carat Weight",
                    "field_type": "number",
                    "validation_rules": {
                        "min": 0,
                        "max": 100,
                        "decimal_places": 2
                    }
                },
                {
                    "field_name": "certification_number",
                    "display_name": "Certification Number",
                    "field_type": "text",
                    "is_searchable": True
                },
                {
                    "field_name": "ring_size",
                    "display_name": "Ring Size",
                    "field_type": "select",
                    "validation_rules": {
                        "options": ["4", "4.5", "5", "5.5", "6", "6.5", "7", "7.5", "8", "8.5", "9", "9.5", "10", "10.5", "11"]
                    }
                }
            ],
            "workflows": [
                {
                    "name": "High-Value Item Security",
                    "trigger": "inventory_adjustment",
                    "conditions": {
                        "value": "> 1000"
                    },
                    "actions": ["require_approval", "log_adjustment", "notify_manager"]
                }
            ]
        },
        
        "automotive": {
            "name": "Automotive Parts",
            "description": "Track compatibility, OEM numbers, and vehicle fitment",
            "custom_fields": [
                {
                    "field_name": "oem_number",
                    "display_name": "OEM Part Number",
                    "field_type": "text",
                    "is_searchable": True,
                    "is_required": True
                },
                {
                    "field_name": "make",
                    "display_name": "Vehicle Make",
                    "field_type": "multi_select",
                    "validation_rules": {
                        "options": ["Toyota", "Honda", "Ford", "Chevrolet", "BMW", "Mercedes", "Audi", "Universal"]
                    },
                    "is_filterable": True
                },
                {
                    "field_name": "model_years",
                    "display_name": "Compatible Years",
                    "field_type": "text",
                    "help_text": "e.g., 2015-2020"
                },
                {
                    "field_name": "position",
                    "display_name": "Position",
                    "field_type": "select",
                    "validation_rules": {
                        "options": ["Front", "Rear", "Left", "Right", "Center", "Universal"]
                    }
                },
                {
                    "field_name": "condition",
                    "display_name": "Condition",
                    "field_type": "select",
                    "validation_rules": {
                        "options": ["New", "Refurbished", "Used", "Remanufactured"]
                    }
                }
            ],
            "workflows": [
                {
                    "name": "Compatibility Check",
                    "trigger": "order_placed",
                    "conditions": {
                        "has_vehicle_info": "true"
                    },
                    "actions": ["verify_compatibility", "flag_if_mismatch"]
                }
            ]
        },
        
        "health_beauty": {
            "name": "Health & Beauty",
            "description": "Manage expiration dates, ingredients, and regulations",
            "custom_fields": [
                {
                    "field_name": "expiry_date",
                    "display_name": "Expiry Date",
                    "field_type": "date",
                    "is_required": True,
                    "is_filterable": True
                },
                {
                    "field_name": "active_ingredients",
                    "display_name": "Active Ingredients",
                    "field_type": "textarea",
                    "is_searchable": True
                },
                {
                    "field_name": "fda_approved",
                    "display_name": "FDA Approved",
                    "field_type": "boolean",
                    "default_value": "false"
                },
                {
                    "field_name": "product_form",
                    "display_name": "Product Form",
                    "field_type": "select",
                    "validation_rules": {
                        "options": ["Liquid", "Cream", "Gel", "Powder", "Capsule", "Tablet", "Spray"]
                    }
                },
                {
                    "field_name": "skin_type",
                    "display_name": "Suitable for Skin Type",
                    "field_type": "multi_select",
                    "validation_rules": {
                        "options": ["All", "Normal", "Dry", "Oily", "Combination", "Sensitive"]
                    }
                }
            ],
            "workflows": [
                {
                    "name": "Expiry Management",
                    "trigger": "daily_check",
                    "conditions": {
                        "days_until_expiry": "< 90"
                    },
                    "actions": ["create_promotion", "prevent_reorder", "notify_team"]
                }
            ]
        }
    }
    
    @classmethod
    def get_template(cls, industry: str) -> Dict[str, Any]:
        """Get template for specific industry"""
        return cls.TEMPLATES.get(industry.lower())
    
    @classmethod
    def list_industries(cls) -> List[str]:
        """Get list of available industries"""
        return list(cls.TEMPLATES.keys())
    
    @classmethod
    def apply_template(cls, industry: str, store_id: int) -> Dict[str, Any]:
        """Apply template to a store (returns configuration to be saved)"""
        template = cls.get_template(industry)
        if not template:
            return None
        
        return {
            "industry": industry,
            "custom_fields": template["custom_fields"],
            "workflows": template.get("workflows", []),
            "applied_at": datetime.utcnow().isoformat()
        }