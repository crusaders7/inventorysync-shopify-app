"""
Bulk metafield operations endpoints.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, File, UploadFile
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import json
import csv
from io import StringIO

from app.core.database import get_db
from app.core.shopify_client import ShopifyClient
from app.core.auth import get_current_shop
from app.models.shop import Shop
from app.core.logging import logger

router = APIRouter()


class MetafieldUpdate(BaseModel):
    """Single metafield update."""
    namespace: str = "custom"
    key: str
    value: str
    type: str = "single_line_text_field"


class ProductMetafieldUpdate(BaseModel):
    """Product metafield bulk update."""
    product_id: str
    metafields: List[MetafieldUpdate]


class BulkUpdateRequest(BaseModel):
    """Bulk update request."""
    updates: List[ProductMetafieldUpdate]


class MetafieldDefinition(BaseModel):
    """Metafield definition."""
    id: str
    name: str
    namespace: str = "custom"
    key: str
    type: str = "single_line_text_field"
    description: Optional[str] = None
    validations: Optional[Dict[str, Any]] = None


class MetafieldTemplate(BaseModel):
    """Metafield template."""
    id: str
    name: str
    description: Optional[str] = None
    industry: Optional[str] = None
    fields: List[MetafieldDefinition]


@router.get("/products/bulk-metafields")
async def get_products_with_metafields(
    shop: Shop = Depends(get_current_shop),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=250),
    query: Optional[str] = None,
    product_type: Optional[List[str]] = Query(None),
    vendor: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db)
):
    """Get products with their metafields for bulk editing."""
    try:
        client = ShopifyClient(shop.shop_domain, shop.access_token)
        
        # Build GraphQL query
        filters = []
        if query:
            filters.append(f'title:*{query}*')
        if product_type:
            filters.append(f'product_type:{" OR ".join(product_type)}')
        if vendor:
            filters.append(f'vendor:{" OR ".join(vendor)}')
        
        filter_query = " AND ".join(filters) if filters else None
        
        # GraphQL query for products with metafields
        graphql_query = """
        query GetProductsWithMetafields($first: Int!, $after: String, $query: String) {
          products(first: $first, after: $after, query: $query) {
            pageInfo {
              hasNextPage
              endCursor
            }
            edges {
              node {
                id
                title
                handle
                productType
                vendor
                featuredImage {
                  url
                }
                variants(first: 1) {
                  edges {
                    node {
                      sku
                    }
                  }
                }
                metafields(first: 100, namespace: "custom") {
                  edges {
                    node {
                      id
                      namespace
                      key
                      value
                      type
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        # Calculate cursor for pagination
        cursor = None
        if page > 1:
            # For simplicity, we'll fetch all previous pages to get the cursor
            # In production, you'd want to cache cursors
            for _ in range(page - 1):
                result = client.graphql(graphql_query, {
                    "first": limit,
                    "after": cursor,
                    "query": filter_query
                })
                data = result.get("data", {}).get("products", {})
                cursor = data.get("pageInfo", {}).get("endCursor")
        
        # Fetch current page
        result = client.graphql(graphql_query, {
            "first": limit,
            "after": cursor,
            "query": filter_query
        })
        
        data = result.get("data", {}).get("products", {})
        products = []
        
        for edge in data.get("edges", []):
            node = edge["node"]
            product = {
                "id": node["id"].split("/")[-1],
                "title": node["title"],
                "handle": node["handle"],
                "product_type": node["productType"],
                "vendor": node["vendor"],
                "image": node["featuredImage"]["url"] if node["featuredImage"] else None,
                "sku": node["variants"]["edges"][0]["node"]["sku"] if node["variants"]["edges"] else None,
                "metafields": {}
            }
            
            # Process metafields
            for mf_edge in node["metafields"]["edges"]:
                mf = mf_edge["node"]
                product["metafields"][mf["key"]] = mf["value"]
            
            products.append(product)
        
        # Get total count (simplified - in production, use a separate count query)
        total = len(products) * page  # Rough estimate
        
        return {
            "products": products,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }
        
    except Exception as e:
        logger.error(f"Error fetching products with metafields: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-update")
async def bulk_update_metafields(
    request: BulkUpdateRequest,
    shop: Shop = Depends(get_current_shop),
    db: Session = Depends(get_db)
):
    """Bulk update metafields for multiple products."""
    try:
        client = ShopifyClient(shop.shop_domain, shop.access_token)
        results = []
        errors = []
        
        for update in request.updates:
            try:
                # Create metafields for each product
                for metafield in update.metafields:
                    mutation = """
                    mutation CreateProductMetafield($input: ProductInput!) {
                      productUpdate(input: $input) {
                        product {
                          id
                        }
                        userErrors {
                          field
                          message
                        }
                      }
                    }
                    """
                    
                    variables = {
                        "input": {
                            "id": f"gid://shopify/Product/{update.product_id}",
                            "metafields": [{
                                "namespace": metafield.namespace,
                                "key": metafield.key,
                                "value": metafield.value,
                                "type": metafield.type
                            }]
                        }
                    }
                    
                    result = client.graphql(mutation, variables)
                    
                    if result.get("data", {}).get("productUpdate", {}).get("userErrors"):
                        errors.append({
                            "product_id": update.product_id,
                            "errors": result["data"]["productUpdate"]["userErrors"]
                        })
                    else:
                        results.append({
                            "product_id": update.product_id,
                            "status": "success"
                        })
                        
            except Exception as e:
                errors.append({
                    "product_id": update.product_id,
                    "error": str(e)
                })
        
        return {
            "success": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error in bulk update: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/definitions")
async def get_metafield_definitions(
    shop: Shop = Depends(get_current_shop),
    db: Session = Depends(get_db)
):
    """Get metafield definitions for the shop."""
    try:
        client = ShopifyClient(shop.shop_domain, shop.access_token)
        
        # Get metafield definitions
        query = """
        query GetMetafieldDefinitions {
          metafieldDefinitions(first: 100, ownerType: PRODUCT) {
            edges {
              node {
                id
                name
                namespace
                key
                type {
                  name
                }
                description
                validations {
                  name
                  value
                }
              }
            }
          }
        }
        """
        
        result = client.graphql(query)
        definitions = []
        
        for edge in result.get("data", {}).get("metafieldDefinitions", {}).get("edges", []):
            node = edge["node"]
            definitions.append({
                "id": node["id"],
                "name": node["name"],
                "namespace": node["namespace"],
                "key": node["key"],
                "type": node["type"]["name"],
                "description": node["description"],
                "validations": [{"name": v["name"], "value": v["value"]} for v in node.get("validations", [])]
            })
        
        # Add some default definitions if none exist
        if not definitions:
            definitions = [
                {
                    "id": "default_1",
                    "name": "Material",
                    "namespace": "custom",
                    "key": "material",
                    "type": "single_line_text_field",
                    "description": "Product material composition"
                },
                {
                    "id": "default_2",
                    "name": "Care Instructions",
                    "namespace": "custom",
                    "key": "care_instructions",
                    "type": "multi_line_text_field",
                    "description": "Product care and maintenance instructions"
                },
                {
                    "id": "default_3",
                    "name": "Warranty Period",
                    "namespace": "custom",
                    "key": "warranty_period",
                    "type": "number_integer",
                    "description": "Warranty period in months"
                }
            ]
        
        return {"definitions": definitions}
        
    except Exception as e:
        logger.error(f"Error fetching metafield definitions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates")
async def get_metafield_templates(
    shop: Shop = Depends(get_current_shop),
    db: Session = Depends(get_db)
):
    """Get predefined metafield templates."""
    # Return predefined templates
    templates = [
        {
            "id": "fashion",
            "name": "Fashion & Apparel",
            "description": "Common fields for clothing and accessories",
            "industry": "fashion",
            "fields": [
                {
                    "id": "fashion_1",
                    "name": "Material",
                    "key": "material",
                    "type": "single_line_text_field",
                    "description": "Fabric or material composition"
                },
                {
                    "id": "fashion_2",
                    "name": "Size Chart",
                    "key": "size_chart",
                    "type": "multi_line_text_field",
                    "description": "Size measurements and fit guide"
                },
                {
                    "id": "fashion_3",
                    "name": "Care Instructions",
                    "key": "care_instructions",
                    "type": "multi_line_text_field",
                    "description": "Washing and care guidelines"
                },
                {
                    "id": "fashion_4",
                    "name": "Color",
                    "key": "color",
                    "type": "color",
                    "description": "Primary color"
                }
            ]
        },
        {
            "id": "electronics",
            "name": "Electronics",
            "description": "Technical specifications for electronic products",
            "industry": "electronics",
            "fields": [
                {
                    "id": "electronics_1",
                    "name": "Warranty Period",
                    "key": "warranty_period",
                    "type": "number_integer",
                    "description": "Warranty in months"
                },
                {
                    "id": "electronics_2",
                    "name": "Technical Specs",
                    "key": "technical_specs",
                    "type": "json",
                    "description": "Detailed technical specifications"
                },
                {
                    "id": "electronics_3",
                    "name": "Power Requirements",
                    "key": "power_requirements",
                    "type": "single_line_text_field",
                    "description": "Voltage and power specifications"
                },
                {
                    "id": "electronics_4",
                    "name": "Dimensions",
                    "key": "dimensions",
                    "type": "dimension",
                    "description": "Product dimensions"
                }
            ]
        },
        {
            "id": "food",
            "name": "Food & Beverage",
            "description": "Nutritional and ingredient information",
            "industry": "food",
            "fields": [
                {
                    "id": "food_1",
                    "name": "Ingredients",
                    "key": "ingredients",
                    "type": "multi_line_text_field",
                    "description": "List of ingredients"
                },
                {
                    "id": "food_2",
                    "name": "Nutritional Info",
                    "key": "nutritional_info",
                    "type": "json",
                    "description": "Nutritional facts per serving"
                },
                {
                    "id": "food_3",
                    "name": "Allergens",
                    "key": "allergens",
                    "type": "multi_line_text_field",
                    "description": "Allergen information"
                },
                {
                    "id": "food_4",
                    "name": "Best Before",
                    "key": "best_before",
                    "type": "date",
                    "description": "Best before date"
                }
            ]
        }
    ]
    
    return {"templates": templates}


@router.post("/import")
async def import_metafields_csv(
    data: List[Dict[str, Any]],
    shop: Shop = Depends(get_current_shop),
    db: Session = Depends(get_db)
):
    """Import metafields from CSV data."""
    try:
        client = ShopifyClient(shop.shop_domain, shop.access_token)
        results = []
        errors = []
        
        for row in data:
            product_id = row.get("Product ID")
            if not product_id:
                errors.append({"row": row, "error": "Missing Product ID"})
                continue
            
            # Extract metafields from row (exclude standard fields)
            standard_fields = ["Product ID", "Title", "SKU", "Product Type", "Vendor"]
            metafields = []
            
            for key, value in row.items():
                if key not in standard_fields and value:
                    metafields.append({
                        "namespace": "custom",
                        "key": key.lower().replace(" ", "_"),
                        "value": value,
                        "type": "single_line_text_field"  # Default type
                    })
            
            if metafields:
                try:
                    # Update product metafields
                    mutation = """
                    mutation UpdateProductMetafields($input: ProductInput!) {
                      productUpdate(input: $input) {
                        product {
                          id
                        }
                        userErrors {
                          field
                          message
                        }
                      }
                    }
                    """
                    
                    variables = {
                        "input": {
                            "id": f"gid://shopify/Product/{product_id}",
                            "metafields": metafields
                        }
                    }
                    
                    result = client.graphql(mutation, variables)
                    
                    if result.get("data", {}).get("productUpdate", {}).get("userErrors"):
                        errors.append({
                            "product_id": product_id,
                            "errors": result["data"]["productUpdate"]["userErrors"]
                        })
                    else:
                        results.append({
                            "product_id": product_id,
                            "metafields_count": len(metafields)
                        })
                        
                except Exception as e:
                    errors.append({
                        "product_id": product_id,
                        "error": str(e)
                    })
        
        return {
            "success": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error importing metafields: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
