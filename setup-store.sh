#!/bin/bash

# InventorySync Store Setup Script
# This script helps you connect your Shopify store to InventorySync

echo "🚀 Starting InventorySync Store Setup..."

# Check if backend server is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Backend server not running on http://localhost:8000"
    echo "Please start the backend server first:"
    echo "  cd backend && source ../venv/bin/activate && python3 -m uvicorn main:app --reload"
    exit 1
fi

# Activate virtual environment and run setup
cd backend
source ../venv/bin/activate
python3 setup_store.py

echo "Setup complete! Check the output above for next steps."