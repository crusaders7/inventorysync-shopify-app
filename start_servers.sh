#!/bin/bash

echo "Starting InventorySync Servers..."
echo "================================"

# Kill any existing servers
echo "Stopping any existing servers..."
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true
sleep 2

# Start backend
echo ""
echo "Starting Backend Server..."
cd /home/brend/inventorysync-shopify-app/backend
source venv/bin/activate
export DATABASE_URL="postgresql://inventorysync:devpassword123@localhost/inventorysync_dev"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 3

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running on http://localhost:8000"
else
    echo "❌ Backend failed to start"
    exit 1
fi

# Start frontend
echo ""
echo "Starting Frontend Server..."
cd /home/brend/inventorysync-shopify-app/frontend
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 3

echo ""
echo "================================"
echo "✅ Both servers are running!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3001"
echo ""
echo "Press Ctrl+C to stop both servers"
echo "================================"

# Wait for Ctrl+C
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
