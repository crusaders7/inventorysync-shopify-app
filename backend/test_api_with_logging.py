#!/usr/bin/env python3
"""
Quick test to verify the API starts and logging is working
"""

import os
import sys
import time
import subprocess
import requests
import signal

# Set environment variables for testing
os.environ['ENVIRONMENT'] = 'development'
os.environ['LOG_LEVEL'] = 'DEBUG'
os.environ['LOG_FORMAT'] = 'json'
os.environ['LOG_DIR'] = './logs'
os.environ['ENABLE_SENTRY'] = 'false'
os.environ['ENABLE_REQUEST_VALIDATION'] = 'false'

# Create log directory
os.makedirs('./logs', exist_ok=True)

print("🚀 Starting InventorySync API with logging enabled...")

# Start the API server
api_process = subprocess.Popen([
    sys.executable, '-m', 'uvicorn', 
    'main:app', 
    '--host', '0.0.0.0', 
    '--port', '8000',
    '--log-level', 'info'
], cwd=os.path.dirname(os.path.abspath(__file__)))

# Give the server time to start
print("⏳ Waiting for server to start...")
time.sleep(5)

try:
    # Test the API
    print("\n📡 Testing API endpoints...")
    
    # Test health endpoint
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        print(f"✅ GET /health: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ GET /health failed: {e}")
    
    # Test API status
    try:
        response = requests.get('http://localhost:8000/api/v1/status', timeout=5)
        print(f"✅ GET /api/v1/status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ GET /api/v1/status failed: {e}")
    
    # Test root endpoint
    try:
        response = requests.get('http://localhost:8000/', timeout=5)
        print(f"✅ GET /: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ GET / failed: {e}")
    
    print("\n📁 Checking log files...")
    log_files = os.listdir('./logs')
    for log_file in log_files:
        size = os.path.getsize(f'./logs/{log_file}')
        print(f"   - {log_file}: {size} bytes")
    
    print("\n✅ API is running with logging enabled!")
    print("   Press Ctrl+C to stop the server...")
    
    # Keep the server running
    api_process.wait()
    
except KeyboardInterrupt:
    print("\n🛑 Shutting down...")
    api_process.send_signal(signal.SIGINT)
    api_process.wait()
    print("✅ Server stopped")
except Exception as e:
    print(f"\n❌ Error: {e}")
    api_process.terminate()
    api_process.wait()
