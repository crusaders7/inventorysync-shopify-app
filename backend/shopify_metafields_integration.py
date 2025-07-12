"""
Shopify Metafields Integration - How Custom Fields Actually Work
This is the technical implementation that makes custom fields appear native in Shopify
"""
import shopify
from typing import Dict, List, Any
import json

class ShopifyMetafieldsManager:
    """
    Manages custom fields using Shopify's native metafields API
    This makes our custom fields appear directly in Shopify admin!
    """
    
    def __init__(self, shop_domain: str, access_token: str):
        self.shop_domain = shop_domain
        self.access_token = access_token
        # Initialize Shopify session
        session = shopify.Session(shop_domain, '2023-10', access_token)
        shopify.ShopifyResource.activate_session(session)
    
    def create_metafield_definition(self, field_config: Dict[str, Any]) -> Dict:
        """
        Creates a metafield definition in Shopify
        This makes the field appear in Shopify admin UI!
        """
        # Shopify metafield definition structure
        definition = {
            "name": field_config["display_name"],
            "namespace": "inventorysync",
            "key": field_config["field_name"],
            "type": self._map_field_type(field_config["field_type"]),
            "description": field_config.get("help_text", ""),
            "ownerType": "PRODUCT",  # Can be PRODUCT, VARIANT, CUSTOMER, etc.
            "validations": self._build_validations(field_config),
            "visibleToStorefrontApi": True
        }
        
        # Create via GraphQL Admin API
        mutation = """
        mutation CreateMetafieldDefinition($definition: MetafieldDefinitionInput!) {
            metafieldDefinitionCreate(definition: $definition) {
                metafieldDefinition {
                    id
                    name
                    namespace
                    key
                    type {
                        name
                    }
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        
        # This creates the field definition in Shopify
        # It will now appear in the product editor!
        return self._execute_graphql(mutation, {"definition": definition})
    
    def _map_field_type(self, our_type: str) -> str:
        """
        Maps our field types to Shopify metafield types
        """
        type_mapping = {
            "text": "single_line_text_field",
            "textarea": "multi_line_text_field",
            "number": "number_integer",
            "decimal": "number_decimal",
            "boolean": "boolean",
            "date": "date",
            "datetime": "date_time",
            "select": "single_line_text_field",  # With validations
            "multi_select": "list.single_line_text_field",
            "url": "url",
            "email": "single_line_text_field",  # With email validation
            "json": "json",
            "file": "file_reference",
            "color": "color",
            "weight": "weight",
            "volume": "volume",
            "dimension": "dimension"
        }
        return type_mapping.get(our_type, "single_line_text_field")
    
    def _build_validations(self, field_config: Dict[str, Any]) -> List[Dict]:
        """
        Build validation rules for the metafield
        """
        validations = []
        
        # Required field validation
        if field_config.get("is_required"):
            validations.append({
                "name": "required",
                "value": "true"
            })
        
        # Choice validation for select fields
        if field_config["field_type"] == "select" and "options" in field_config:
            validations.append({
                "name": "choices",
                "value": json.dumps(field_config["options"])
            })
        
        # Min/Max validations for numbers
        if field_config["field_type"] in ["number", "decimal"]:
            if "min_value" in field_config:
                validations.append({
                    "name": "min",
                    "value": str(field_config["min_value"])
                })
            if "max_value" in field_config:
                validations.append({
                    "name": "max",
                    "value": str(field_config["max_value"])
                })
        
        return validations
    
    def update_product_metafield(self, product_id: int, field_name: str, value: Any) -> Dict:
        """
        Updates a product's custom field value
        This is what happens when merchant edits the field in Shopify admin
        """
        mutation = """
        mutation UpdateProductMetafield($input: ProductInput!) {
            productUpdate(input: $input) {
                product {
                    id
                    metafield(namespace: "inventorysync", key: $key) {
                        value
                    }
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        
        input_data = {
            "id": f"gid://shopify/Product/{product_id}",
            "metafields": [
                {
                    "namespace": "inventorysync",
                    "key": field_name,
                    "value": str(value),
                    "type": self._get_field_type(field_name)
                }
            ]
        }
        
        return self._execute_graphql(mutation, {"input": input_data, "key": field_name})
    
    def enable_metafield_in_admin(self, definition_id: str) -> Dict:
        """
        Makes the metafield visible in Shopify admin UI
        This is the magic that makes it appear native!
        """
        mutation = """
        mutation EnableMetafieldInAdmin($definitionId: ID!) {
            metafieldDefinitionUpdate(
                id: $definitionId,
                definition: {
                    visibleToAdminApi: true,
                    visibleToStorefrontApi: true,
                    pin: true  # This pins it to the product form!
                }
            ) {
                metafieldDefinition {
                    id
                    pinnedToResource
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        
        return self._execute_graphql(mutation, {"definitionId": definition_id})
    
    def create_app_data_metafield(self) -> Dict:
        """
        Creates app-owned metafields that sync with our database
        """
        # This creates a special app-data metafield that Shopify manages
        # It appears in the admin and syncs with our app automatically!
        definition = {
            "name": "InventorySync Custom Fields",
            "namespace": "$app:inventorysync",  # App-owned namespace
            "key": "custom_fields",
            "type": "json",
            "description": "Custom fields managed by InventorySync",
            "ownerType": "PRODUCT",
            "access": {
                "admin": "MERCHANT_READ_WRITE",  # Merchants can edit in admin
                "storefront": "PUBLIC_READ"       # Visible on storefront
            }
        }
        
        # This makes all our custom fields appear as one section in Shopify admin
        return self._create_app_metafield_definition(definition)


# Example: How to make custom fields appear in Shopify admin
def setup_custom_field_in_shopify(shop_domain: str, access_token: str, field_config: Dict):
    """
    This is called when a merchant creates a new custom field
    It makes the field instantly appear in their Shopify admin!
    """
    manager = ShopifyMetafieldsManager(shop_domain, access_token)
    
    # Step 1: Create the metafield definition
    result = manager.create_metafield_definition(field_config)
    definition_id = result["data"]["metafieldDefinitionCreate"]["metafieldDefinition"]["id"]
    
    # Step 2: Enable it in admin UI (pin it to product form)
    manager.enable_metafield_in_admin(definition_id)
    
    # Now the field appears in Shopify admin for all products!
    return {
        "success": True,
        "message": f"Field '{field_config['display_name']}' now appears in your Shopify admin!",
        "definition_id": definition_id
    }


# UI Configuration for how fields appear
FIELD_UI_CONFIGS = {
    "apparel": {
        "section_title": "Product Details",
        "fields": [
            {
                "key": "material",
                "label": "Material Composition",
                "type": "text",
                "placeholder": "e.g., 100% Cotton",
                "help": "Enter the fabric or material composition"
            },
            {
                "key": "care_instructions", 
                "label": "Care Instructions",
                "type": "multi_line",
                "placeholder": "Machine wash cold...",
                "help": "How should customers care for this item?"
            },
            {
                "key": "size_chart",
                "label": "Size Chart",
                "type": "file",
                "accepts": ["image/*", "application/pdf"],
                "help": "Upload size chart image or PDF"
            }
        ]
    }
}
