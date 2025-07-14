"""
Shopify Sync Service
Handles syncing data from Shopify stores
"""

import logging
from typing import List, Dict, Optional
from simple_models import SessionLocal, Store, Product, InventoryItem, Alert
from shopify_client import ShopifyClient

logger = logging.getLogger(__name__)

class ShopifySync:
    """Service for syncing data from Shopify"""
    
    def __init__(self, shop_domain: str):
        self.shop_domain = shop_domain.replace('.myshopify.com', '')
        self.db = SessionLocal()
        self.store = None
        self.client = None
        
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    async def initialize(self):
        """Initialize the sync service with store data"""
        self.store = self.db.query(Store).filter(
            Store.shopify_domain == f"{self.shop_domain}.myshopify.com"
        ).first()
        
        if not self.store:
            raise ValueError(f"Store not found: {self.shop_domain}")
        
        if not self.store.access_token:
            raise ValueError(f"No access token for store: {self.shop_domain}")
        
        self.client = ShopifyClient(self.shop_domain, self.store.access_token)
        logger.info(f"Initialized sync for store: {self.store.shop_name}")
    
    async def sync_products(self) -> Dict:
        """Sync products from Shopify"""
        if not self.client:
            await self.initialize()
        
        try:
            logger.info("Starting product sync...")
            
            # Get products from Shopify
            response = await self.client.get_products(limit=250)
            products_data = response.get('products', [])
            
            synced_count = 0
            updated_count = 0
            
            for product_data in products_data:
                # Check if product exists
                existing_product = self.db.query(Product).filter(
                    Product.shopify_id == str(product_data['id'])
                ).first()
                
                if existing_product:
                    # Update existing product
                    existing_product.title = product_data.get('title', '')
                    existing_product.handle = product_data.get('handle', '')
                    existing_product.product_type = product_data.get('product_type', '')
                    existing_product.vendor = product_data.get('vendor', '')
                    existing_product.status = product_data.get('status', 'active')
                    updated_count += 1
                else:
                    # Create new product
                    new_product = Product(
                        shopify_id=str(product_data['id']),
                        store_id=self.store.id,
                        title=product_data.get('title', ''),
                        handle=product_data.get('handle', ''),
                        product_type=product_data.get('product_type', ''),
                        vendor=product_data.get('vendor', ''),
                        status=product_data.get('status', 'active')
                    )
                    self.db.add(new_product)
                    synced_count += 1
                
                # Sync variants as inventory items
                for variant in product_data.get('variants', []):
                    await self._sync_variant(product_data, variant)
            
            self.db.commit()
            
            result = {
                'products_synced': synced_count,
                'products_updated': updated_count,
                'total_products': len(products_data)
            }
            
            logger.info(f"Product sync completed: {result}")
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Product sync failed: {str(e)}")
            raise
    
    async def _sync_variant(self, product_data: Dict, variant_data: Dict):
        """Sync a product variant as an inventory item"""
        try:
            existing_item = self.db.query(InventoryItem).filter(
                InventoryItem.shopify_id == str(variant_data['id'])
            ).first()
            
            # Determine stock status
            quantity = variant_data.get('inventory_quantity', 0)
            reorder_point = 10  # Default reorder point
            
            if quantity == 0:
                status = "out_of_stock"
            elif quantity < reorder_point:
                status = "low_stock"
            elif quantity > reorder_point * 5:
                status = "overstock"
            else:
                status = "normal"
            
            if existing_item:
                # Update existing item
                existing_item.sku = variant_data.get('sku', '')
                existing_item.title = f"{product_data.get('title', '')} - {variant_data.get('title', '')}"
                existing_item.inventory_quantity = quantity
                existing_item.status = status
            else:
                # Create new inventory item
                new_item = InventoryItem(
                    shopify_id=str(variant_data['id']),
                    product_id=product_data['id'],
                    variant_id=str(variant_data['id']),
                    sku=variant_data.get('sku', ''),
                    title=f"{product_data.get('title', '')} - {variant_data.get('title', '')}",
                    inventory_quantity=quantity,
                    location_name="Main Location",
                    status=status
                )
                self.db.add(new_item)
                
                # Create alert if needed
                if status in ['low_stock', 'out_of_stock']:
                    await self._create_alert(new_item, status)
                    
        except Exception as e:
            logger.error(f"Failed to sync variant {variant_data.get('id')}: {str(e)}")
    
    async def _create_alert(self, inventory_item: InventoryItem, alert_type: str):
        """Create an alert for inventory issues"""
        try:
            # Check if alert already exists
            existing_alert = self.db.query(Alert).filter(
                Alert.inventory_item_id == inventory_item.id,
                Alert.alert_type == alert_type,
                Alert.status == 'active'
            ).first()
            
            if existing_alert:
                return  # Alert already exists
            
            # Create new alert
            if alert_type == 'out_of_stock':
                title = 'Out of Stock'
                message = f'{inventory_item.title} is out of stock'
                severity = 'critical'
            elif alert_type == 'low_stock':
                title = 'Low Stock Alert'
                message = f'{inventory_item.title} has low stock ({inventory_item.inventory_quantity} units)'
                severity = 'warning'
            else:
                return
            
            new_alert = Alert(
                store_id=self.store.id,
                inventory_item_id=inventory_item.id,
                alert_type=alert_type,
                title=title,
                message=message,
                severity=severity,
                status='active'
            )
            self.db.add(new_alert)
            
        except Exception as e:
            logger.error(f"Failed to create alert: {str(e)}")
    
    async def get_inventory_stats(self) -> Dict:
        """Get real inventory statistics"""
        try:
            total_products = self.db.query(Product).filter(Product.store_id == self.store.id).count()
            total_items = self.db.query(InventoryItem).count()
            
            low_stock_count = self.db.query(InventoryItem).filter(
                InventoryItem.status == 'low_stock'
            ).count()
            
            out_of_stock_count = self.db.query(InventoryItem).filter(
                InventoryItem.status == 'out_of_stock'
            ).count()
            
            total_value = self.db.query(InventoryItem).with_entities(
                self.db.query(InventoryItem.inventory_quantity).label('total_qty')
            ).scalar() or 0
            
            total_value = total_value * 50  # Assume $50 average per item
            
            return {
                'totalProducts': total_products,
                'lowStockAlerts': low_stock_count + out_of_stock_count,
                'totalValue': total_value,
                'activeLocations': 1,  # For now
                'outOfStockCount': out_of_stock_count,
                'lowStockCount': low_stock_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get inventory stats: {str(e)}")
            return {
                'totalProducts': 0,
                'lowStockAlerts': 0,
                'totalValue': 0,
                'activeLocations': 0
            }

# Utility function
async def sync_shopify_store(shop_domain: str) -> Dict:
    """Sync a Shopify store's data"""
    async with ShopifySync(shop_domain) as sync_service:
        await sync_service.initialize()
        result = await sync_service.sync_products()
        return result