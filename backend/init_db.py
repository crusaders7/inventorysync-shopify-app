#!/usr/bin/env python3
"""
Initialize database tables
"""

import os
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./inventorysync_dev.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create base
Base = declarative_base()

# Import models to register them
from models import Store, Product, ProductVariant, InventoryItem, InventoryLevel, Location, Alert, Forecast, Supplier, PurchaseOrder, PurchaseOrderItem, Settings

# Create all tables
Base.metadata.create_all(bind=engine)
print(f"✅ Database tables created successfully!")
print(f"📁 Database location: {DATABASE_URL}")