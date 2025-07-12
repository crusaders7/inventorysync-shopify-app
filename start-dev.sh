#!/bin/bash

# InventorySync Development Start Script
echo "🚀 Starting InventorySync Development Environment..."

# Check if backend virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "⚠️  Backend virtual environment not found. Creating..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
else
    echo "✅ Backend virtual environment found"
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "⚠️  Frontend dependencies not found. Installing..."
    cd frontend
    npm install
    cd ..
else
    echo "✅ Frontend dependencies found"
fi

# Start the services
echo ""
echo "📦 Starting services..."
echo "-----------------------------------"
echo "Backend API: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "-----------------------------------"
echo ""

# Use concurrently to run both services
npm run dev:all