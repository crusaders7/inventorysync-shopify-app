#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🛠️ Setting up development environment...${NC}"

# Check if running from correct directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}Error: Must be run from project root${NC}"
    exit 1
fi

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
npm install

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install dependencies${NC}"
    exit 1
fi

# Setup environment if not exists
if [ ! -f ".env.local" ]; then
    echo -e "${YELLOW}Creating .env.local...${NC}"
    echo "BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000" > .env.local
fi

# Start development server
echo -e "${GREEN}Starting development server...${NC}"
npm run dev
