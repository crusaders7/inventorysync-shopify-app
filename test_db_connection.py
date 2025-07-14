#!/usr/bin/env python3
"""Test database connectivity for Railway PostgreSQL and Redis services."""

import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Load environment variables from backend/.env
from dotenv import load_dotenv
env_path = backend_dir / ".env"
load_dotenv(env_path)

print("Testing Railway Database Connections...")
print("=" * 50)

# Test PostgreSQL connection
print("\n1. Testing PostgreSQL connection...")
try:
    import psycopg2
    from urllib.parse import urlparse
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment variables")
    else:
        print(f"   Connecting to: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")
        
        # Parse the URL
        result = urlparse(DATABASE_URL)
        
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        
        # Test the connection
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"✅ PostgreSQL connected successfully!")
        print(f"   Version: {version[0].split(',')[0]}")
        
        # Check if we can create tables
        cur.execute("SELECT current_database();")
        db_name = cur.fetchone()
        print(f"   Database: {db_name[0]}")
        
        cur.close()
        conn.close()
        
except ImportError:
    print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
except Exception as e:
    print(f"❌ PostgreSQL connection failed: {str(e)}")

# Test Redis connection
print("\n2. Testing Redis connection...")
try:
    import redis
    
    REDIS_URL = os.getenv("REDIS_URL")
    if not REDIS_URL:
        print("❌ REDIS_URL not found in environment variables")
    else:
        print(f"   Connecting to: {REDIS_URL.split('@')[1] if '@' in REDIS_URL else REDIS_URL}")
        
        # Connect to Redis
        r = redis.from_url(REDIS_URL)
        
        # Test the connection
        r.ping()
        print("✅ Redis connected successfully!")
        
        # Test basic operations
        r.set("test_key", "test_value", ex=10)  # expires in 10 seconds
        value = r.get("test_key")
        if value == b"test_value":
            print("   Read/Write test: Passed")
        
        # Get Redis info
        info = r.info()
        print(f"   Redis version: {info.get('redis_version', 'Unknown')}")
        print(f"   Used memory: {info.get('used_memory_human', 'Unknown')}")
        
except ImportError:
    print("❌ redis not installed. Run: pip install redis")
except Exception as e:
    print(f"❌ Redis connection failed: {str(e)}")

print("\n" + "=" * 50)
print("Connection test completed!")
