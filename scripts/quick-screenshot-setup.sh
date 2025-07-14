#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=== Quick Screenshot Setup ===${NC}"

# Kill any existing servers
echo "Cleaning up old processes..."
pkill -f "uvicorn" 2>/dev/null
pkill -f "vite" 2>/dev/null
sleep 2

# Start backend
echo -e "\n${YELLOW}Starting backend server...${NC}"
cd /home/brend/inventorysync-shopify-app/backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Start frontend
echo -e "${YELLOW}Starting frontend server...${NC}"
cd /home/brend/inventorysync-shopify-app/frontend
npm run dev &
FRONTEND_PID=$!

# Wait for servers
echo -e "\nWaiting for servers to start..."
sleep 8

# Check status
echo -e "\n${GREEN}=== Server Status ===${NC}"
if curl -s http://localhost:8000 > /dev/null 2>&1; then
    echo "✅ Backend: http://localhost:8000"
else
    echo "❌ Backend not running"
fi

if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend: http://localhost:3000"
else
    echo "❌ Frontend not running"
fi

echo -e "\n${GREEN}=== Screenshot Instructions ===${NC}"
echo -e "The app is running at: ${BLUE}http://localhost:3000${NC}"
echo ""
echo "Take screenshots of:"
echo "1. Dashboard - http://localhost:3000/"
echo "2. Custom Fields - http://localhost:3000/custom-fields"
echo "3. Inventory - http://localhost:3000/inventory"
echo "4. Reports - http://localhost:3000/reports"
echo "5. Settings - http://localhost:3000/settings"
echo ""
echo -e "${YELLOW}Save screenshots to:${NC}"
echo "/home/brend/inventorysync-shopify-app/app-submission-assets/screenshots/"
echo ""
echo "Press Ctrl+C to stop servers when done."

# Keep script running
wait
