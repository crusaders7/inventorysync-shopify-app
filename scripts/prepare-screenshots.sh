#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== InventorySync App Store Asset Preparation ===${NC}"
echo ""

# Create directories
mkdir -p /home/brend/inventorysync-shopify-app/app-submission-assets/screenshots
mkdir -p /home/brend/inventorysync-shopify-app/app-submission-assets/icons
mkdir -p /home/brend/inventorysync-shopify-app/app-submission-assets/banners

# Step 1: Check dependencies
echo -e "${YELLOW}Step 1: Checking dependencies...${NC}"
if ! command -v convert &> /dev/null; then
    echo "ImageMagick not found. Installing..."
    sudo apt-get update && sudo apt-get install -y imagemagick
fi

if ! command -v google-chrome &> /dev/null; then
    echo "Chrome not found. Installing Chrome for screenshots..."
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
    sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
    sudo apt-get update && sudo apt-get install -y google-chrome-stable
fi

# Step 2: Start the development server
echo -e "${YELLOW}Step 2: Starting development servers...${NC}"

# Start backend
cd /home/brend/inventorysync-shopify-app/backend
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Kill any existing servers
pkill -f "uvicorn" 2>/dev/null
pkill -f "vite" 2>/dev/null

# Start backend in background
echo "Starting backend server..."
python -m uvicorn app.main:app --reload --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!

# Start frontend
cd /home/brend/inventorysync-shopify-app/frontend
echo "Starting frontend server..."
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for servers to start
echo "Waiting for servers to start..."
sleep 10

# Check if servers are running
if ! curl -s http://localhost:8000 > /dev/null; then
    echo -e "${YELLOW}Backend might not be running. Check /tmp/backend.log${NC}"
fi

if ! curl -s http://localhost:5173 > /dev/null; then
    echo -e "${YELLOW}Frontend might not be running. Check /tmp/frontend.log${NC}"
fi

echo -e "${GREEN}✓ Development servers started${NC}"
echo ""
echo -e "${BLUE}=== SCREENSHOT INSTRUCTIONS ===${NC}"
echo ""
echo "The app is now running at: ${GREEN}http://localhost:5173${NC}"
echo ""
echo "Please take screenshots of these pages:"
echo "1. Dashboard - http://localhost:5173/"
echo "2. Custom Fields Manager - http://localhost:5173/custom-fields"
echo "3. Product Edit with Custom Fields"
echo "4. Bulk Operations"
echo "5. Industry Templates"
echo "6. Search & Filter"
echo "7. Analytics/Reports"
echo ""
echo -e "${YELLOW}IMPORTANT: Save all screenshots to:${NC}"
echo -e "${GREEN}/home/brend/inventorysync-shopify-app/app-submission-assets/screenshots/${NC}"
echo ""
echo "Name them as:"
echo "- 01-dashboard.png"
echo "- 02-field-builder.png"
echo "- 03-product-edit.png"
echo "- 04-bulk-operations.png"
echo "- 05-templates.png"
echo "- 06-search-filter.png"
echo "- 07-analytics.png"
echo ""
echo -e "${BLUE}Once you've saved all screenshots, press ENTER to continue...${NC}"
read -p ""

# Step 3: Convert SVG icons to PNG
echo -e "${YELLOW}Step 3: Converting icons to PNG...${NC}"

# Convert app icon
convert -background none -resize 1024x1024 \
    /home/brend/inventorysync-shopify-app/frontend/public/app-icon.svg \
    /home/brend/inventorysync-shopify-app/app-submission-assets/icons/app-icon-1024.png

# Create additional icon sizes
convert -background none -resize 512x512 \
    /home/brend/inventorysync-shopify-app/frontend/public/app-icon.svg \
    /home/brend/inventorysync-shopify-app/app-submission-assets/icons/app-icon-512.png

convert -background none -resize 256x256 \
    /home/brend/inventorysync-shopify-app/frontend/public/app-icon.svg \
    /home/brend/inventorysync-shopify-app/app-submission-assets/icons/app-icon-256.png

convert -background none -resize 128x128 \
    /home/brend/inventorysync-shopify-app/frontend/public/app-icon.svg \
    /home/brend/inventorysync-shopify-app/app-submission-assets/icons/app-icon-128.png

# Convert favicon
convert -background none -resize 32x32 \
    /home/brend/inventorysync-shopify-app/frontend/public/favicon.svg \
    /home/brend/inventorysync-shopify-app/app-submission-assets/icons/favicon-32.png

echo -e "${GREEN}✓ Icons converted to PNG${NC}"

# Step 4: Generate app banner
echo -e "${YELLOW}Step 4: Generating app banner...${NC}"

# Use headless Chrome to capture the banner
google-chrome --headless --disable-gpu --window-size=1920,1080 \
    --screenshot=/home/brend/inventorysync-shopify-app/app-submission-assets/banners/app-banner.png \
    file:///home/brend/inventorysync-shopify-app/app-submission-assets/app-banner-preview.html

echo -e "${GREEN}✓ App banner generated${NC}"

# Step 5: Process screenshots
echo -e "${YELLOW}Step 5: Processing screenshots...${NC}"

# Check if screenshots exist
SCREENSHOT_DIR="/home/brend/inventorysync-shopify-app/app-submission-assets/screenshots"
if [ -f "$SCREENSHOT_DIR/01-dashboard.png" ]; then
    echo "Processing screenshots..."
    
    # Ensure screenshots are exactly 1280x800 (Shopify requirement)
    for file in $SCREENSHOT_DIR/*.png; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            convert "$file" -resize 1280x800! "$SCREENSHOT_DIR/processed-$filename"
            echo "Processed: $filename"
        fi
    done
    
    echo -e "${GREEN}✓ Screenshots processed${NC}"
else
    echo -e "${YELLOW}No screenshots found in $SCREENSHOT_DIR${NC}"
fi

# Step 6: Clean up
echo -e "${YELLOW}Step 6: Cleaning up...${NC}"

# Kill the development servers
kill $BACKEND_PID 2>/dev/null
kill $FRONTEND_PID 2>/dev/null

echo -e "${GREEN}✓ Development servers stopped${NC}"

# Step 7: Generate final report
echo -e "${BLUE}=== ASSET GENERATION COMPLETE ===${NC}"
echo ""
echo "Generated assets location:"
echo "- Icons: /home/brend/inventorysync-shopify-app/app-submission-assets/icons/"
echo "- Banner: /home/brend/inventorysync-shopify-app/app-submission-assets/banners/"
echo "- Screenshots: /home/brend/inventorysync-shopify-app/app-submission-assets/screenshots/"
echo ""
echo -e "${GREEN}All assets are ready for Shopify App Store submission!${NC}"
