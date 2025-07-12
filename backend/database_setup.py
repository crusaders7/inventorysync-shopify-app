"""
Database Setup and Migration Management
Production-ready database initialization and migration utilities
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from sqlalchemy import text, inspect
from alembic.config import Config
from alembic import command
from alembic.runtime.migration import MigrationContext
from alembic.operations import Operations

from database import AsyncSessionLocal, async_engine, init_db, DatabaseManager
from models import Base, Store, Location, Product, ProductVariant, InventoryItem
from config import settings, is_development, is_production
from utils.logging import logger

class DatabaseSetup:
    """Database setup and migration management"""
    
    def __init__(self):
        self.logger = logger
    
    async def check_database_exists(self) -> bool:
        """Check if database exists and is accessible"""
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            self.logger.error(f"Database check failed: {e}")
            return False
    
    async def check_tables_exist(self) -> bool:
        """Check if core tables exist"""
        try:
            async with async_engine.begin() as conn:
                # Check if stores table exists
                result = await conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name='stores'")
                    if "sqlite" in str(async_engine.url) else
                    text("SELECT table_name FROM information_schema.tables WHERE table_name='stores'")
                )
                return result.fetchone() is not None
        except Exception as e:
            self.logger.error(f"Table check failed: {e}")
            return False
    
    async def create_database_schema(self):
        """Create all database tables"""
        try:
            self.logger.info("Creating database schema...")
            
            async with async_engine.begin() as conn:
                # Create all tables
                await conn.run_sync(Base.metadata.create_all)
            
            self.logger.info("Database schema created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create database schema: {e}")
            raise
    
    async def seed_development_data(self):
        """Seed database with development data"""
        if not is_development():
            self.logger.warning("Attempted to seed data in non-development environment")
            return
        
        try:
            self.logger.info("Seeding development data...")
            
            async with AsyncSessionLocal() as session:
                # Check if data already exists
                existing_store = await session.execute(
                    text("SELECT COUNT(*) FROM stores")
                )
                if existing_store.scalar() > 0:
                    self.logger.info("Development data already exists")
                    return
                
                # Create development store
                dev_store = Store(
                    shopify_store_id="dev-store-123",
                    shop_domain="dev-store.myshopify.com",
                    store_name="Development Store",
                    currency="USD",
                    timezone="UTC",
                    subscription_plan="pro",
                    subscription_status="active",
                    access_token="dev_access_token_123"
                )
                session.add(dev_store)
                await session.commit()
                await session.refresh(dev_store)
                
                # Create locations
                warehouse_a = Location(
                    store_id=dev_store.id,
                    shopify_location_id="loc_warehouse_a",
                    name="Warehouse A",
                    address="123 Storage St",
                    city="Warehouse City",
                    country="US",
                    is_active=True,
                    manages_inventory=True
                )
                
                warehouse_b = Location(
                    store_id=dev_store.id,
                    shopify_location_id="loc_warehouse_b", 
                    name="Warehouse B",
                    address="456 Storage Ave",
                    city="Storage Town",
                    country="US",
                    is_active=True,
                    manages_inventory=True
                )
                
                retail_store = Location(
                    store_id=dev_store.id,
                    shopify_location_id="loc_retail_1",
                    name="Retail Store Downtown",
                    address="789 Main St",
                    city="Downtown",
                    country="US",
                    is_active=True,
                    manages_inventory=True
                )
                
                session.add_all([warehouse_a, warehouse_b, retail_store])
                await session.commit()
                await session.refresh(warehouse_a)
                await session.refresh(warehouse_b)
                await session.refresh(retail_store)
                
                # Create sample products
                t_shirt = Product(
                    store_id=dev_store.id,
                    shopify_product_id="prod_tshirt_001",
                    title="Premium Cotton T-Shirt",
                    handle="premium-cotton-tshirt",
                    product_type="Apparel",
                    vendor="Cotton Co",
                    price=29.99,
                    cost_per_item=12.50,
                    status="active"
                )
                
                sneakers = Product(
                    store_id=dev_store.id,
                    shopify_product_id="prod_sneaker_001", 
                    title="Running Sneakers",
                    handle="running-sneakers",
                    product_type="Footwear",
                    vendor="SportsCorp",
                    price=89.99,
                    cost_per_item=45.00,
                    status="active"
                )
                
                hat = Product(
                    store_id=dev_store.id,
                    shopify_product_id="prod_hat_001",
                    title="Baseball Cap",
                    handle="baseball-cap",
                    product_type="Accessories",
                    vendor="CapMakers Inc",
                    price=24.99,
                    cost_per_item=8.75,
                    status="active"
                )
                
                session.add_all([t_shirt, sneakers, hat])
                await session.commit()
                await session.refresh(t_shirt)
                await session.refresh(sneakers)
                await session.refresh(hat)
                
                # Create product variants
                t_shirt_variants = [
                    ProductVariant(
                        product_id=t_shirt.id,
                        shopify_variant_id=f"var_tshirt_{size}",
                        title=f"Size {size}",
                        sku=f"BTS-{size}-001",
                        price=29.99,
                        cost_per_item=12.50,
                        weight=0.2,
                        track_inventory=True
                    ) for size in ["S", "M", "L", "XL"]
                ]
                
                sneaker_variants = [
                    ProductVariant(
                        product_id=sneakers.id,
                        shopify_variant_id=f"var_sneaker_{size}",
                        title=f"Size {size}",
                        sku=f"RSN-{size}-001",
                        price=89.99,
                        cost_per_item=45.00,
                        weight=0.8,
                        track_inventory=True
                    ) for size in ["38", "39", "40", "41", "42", "43", "44"]
                ]
                
                hat_variant = ProductVariant(
                    product_id=hat.id,
                    shopify_variant_id="var_hat_onesize",
                    title="One Size",
                    sku="GH-001",
                    price=24.99,
                    cost_per_item=8.75,
                    weight=0.15,
                    track_inventory=True
                )
                
                session.add_all(t_shirt_variants + sneaker_variants + [hat_variant])
                await session.commit()
                
                # Create inventory items with different stock levels
                all_variants = t_shirt_variants + sneaker_variants + [hat_variant]
                locations = [warehouse_a, warehouse_b, retail_store]
                
                for variant in all_variants:
                    for location in locations:
                        # Vary stock levels for testing
                        if variant.sku == "BTS-M-001":  # Low stock
                            stock = 5
                        elif variant.sku == "RSN-42-001":  # Out of stock
                            stock = 0
                        elif variant.sku == "GH-001":  # Overstock
                            stock = 150
                        else:
                            stock = 25  # Normal stock
                        
                        inventory_item = InventoryItem(
                            store_id=dev_store.id,
                            location_id=location.id,
                            variant_id=variant.id,
                            available_quantity=stock,
                            on_hand_quantity=stock,
                            reorder_point=10,
                            reorder_quantity=50,
                            lead_time_days=7
                        )
                        session.add(inventory_item)
                
                await session.commit()
                
                self.logger.info("Development data seeded successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to seed development data: {e}")
            raise
    
    async def setup_database(self, seed_data: bool = False):
        """Complete database setup"""
        try:
            self.logger.info("Starting database setup...")
            
            # Check if database is accessible
            if not await self.check_database_exists():
                raise Exception("Cannot connect to database")
            
            # Create schema if tables don't exist
            if not await self.check_tables_exist():
                await self.create_database_schema()
            else:
                self.logger.info("Database tables already exist")
            
            # Seed development data if requested
            if seed_data and is_development():
                await self.seed_development_data()
            
            self.logger.info("Database setup completed successfully")
            
        except Exception as e:
            self.logger.error(f"Database setup failed: {e}")
            raise
    
    async def reset_database(self):
        """Reset database (development only)"""
        if not is_development():
            raise RuntimeError("Database reset is only allowed in development")
        
        try:
            self.logger.warning("Resetting database...")
            await DatabaseManager.reset_database()
            self.logger.info("Database reset completed")
            
        except Exception as e:
            self.logger.error(f"Database reset failed: {e}")
            raise
    
    async def check_database_health(self) -> dict:
        """Comprehensive database health check"""
        health_status = {
            "database_accessible": False,
            "tables_exist": False,
            "sample_query": False,
            "connection_pool": False,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Check database accessibility
            health_status["database_accessible"] = await self.check_database_exists()
            
            # Check if tables exist
            health_status["tables_exist"] = await self.check_tables_exist()
            
            # Run sample query
            if health_status["tables_exist"]:
                async with AsyncSessionLocal() as session:
                    result = await session.execute(text("SELECT COUNT(*) FROM stores"))
                    store_count = result.scalar()
                    health_status["sample_query"] = True
                    health_status["store_count"] = store_count
            
            # Check connection pool status
            health_status["connection_pool"] = async_engine.pool.checkedin() >= 0
            
            self.logger.info("Database health check completed", extra=health_status)
            
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            health_status["error"] = str(e)
        
        return health_status


async def main():
    """CLI for database setup"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Setup CLI")
    parser.add_argument("--setup", action="store_true", help="Setup database")
    parser.add_argument("--seed", action="store_true", help="Seed with development data")
    parser.add_argument("--reset", action="store_true", help="Reset database (dev only)")
    parser.add_argument("--health", action="store_true", help="Check database health")
    
    args = parser.parse_args()
    
    db_setup = DatabaseSetup()
    
    try:
        if args.setup:
            await db_setup.setup_database(seed_data=args.seed)
        elif args.reset:
            await db_setup.reset_database()
        elif args.health:
            health = await db_setup.check_database_health()
            print(f"Database Health: {health}")
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(f"Database operation failed: {e}")
        sys.exit(1)
    finally:
        await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())