#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Starting deployment of Next.js Frontend...${NC}"

# Check if running from correct directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}Error: Must be run from project root${NC}"
    exit 1
fi

# Load environment variables
if [ -f ".env.local" ]; then
    echo -e "${GREEN}Loading environment variables...${NC}"
    source .env.local
else
    echo -e "${YELLOW}Warning: .env.local not found${NC}"
fi

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
npm install

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install dependencies${NC}"
    exit 1
fi

# Build application
echo -e "${GREEN}Building application...${NC}"
npm run build

if [ $? -ne 0 ]; then
    echo -e "${RED}Build failed${NC}"
    exit 1
fi

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    echo -e "${YELLOW}PM2 not found. Installing...${NC}"
    npm install -g pm2
fi

# Start/Restart PM2 process
echo -e "${GREEN}Starting application...${NC}"
pm2 describe "inventorysync-frontend" > /dev/null
if [ $? -eq 0 ]; then
    pm2 restart "inventorysync-frontend"
else
    pm2 start npm --name "inventorysync-frontend" -- start
fi

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "${GREEN}📝 Logs available with: pm2 logs inventorysync-frontend${NC}"
