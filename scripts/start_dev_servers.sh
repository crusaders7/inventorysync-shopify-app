#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting InventorySync Development Servers${NC}"
echo "================================================"

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo -e "${RED}❌ PostgreSQL is not running!${NC}"
    echo "Please start PostgreSQL first: sudo service postgresql start"
    exit 1
fi

# Function to run backend
start_backend() {
    echo -e "\n${GREEN}Starting Backend Server...${NC}"
    cd /home/brend/inventorysync-shopify-app/backend
    source venv/bin/activate
    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
}

# Function to run frontend
start_frontend() {
    echo -e "\n${GREEN}Starting Frontend Server...${NC}"
    cd /home/brend/inventorysync-shopify-app/frontend
    npm run dev
}

# Create a new terminal for backend if possible
if command -v gnome-terminal &> /dev/null; then
    echo -e "${BLUE}Opening backend in new terminal...${NC}"
    gnome-terminal -- bash -c "cd /home/brend/inventorysync-shopify-app/backend && source venv/bin/activate && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload; exec bash"
elif command -v xterm &> /dev/null; then
    echo -e "${BLUE}Opening backend in new terminal...${NC}"
    xterm -e "cd /home/brend/inventorysync-shopify-app/backend && source venv/bin/activate && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload; exec bash" &
else
    echo -e "${BLUE}Starting backend in background...${NC}"
    start_backend &
    BACKEND_PID=$!
    echo "Backend PID: $BACKEND_PID"
fi

# Give backend time to start
echo -e "${BLUE}Waiting for backend to start...${NC}"
sleep 5

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ Backend is running!${NC}"
else
    echo -e "${RED}⚠️  Backend might not be ready yet${NC}"
fi

# Start frontend in current terminal
start_frontend

# If we started backend in background, kill it when frontend stops
if [ ! -z "$BACKEND_PID" ]; then
    echo -e "\n${BLUE}Stopping backend server...${NC}"
    kill $BACKEND_PID
fi
